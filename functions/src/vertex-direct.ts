/**
 * Vertex AI Search Client (Direct Integration)
 *
 * Directly calls Google Cloud Vertex AI Search (Discovery Engine)
 * Returns search results WITHOUT LLM summaries to stay within free quota.
 * The Python server will generate answers using Gemini based on these results.
 */

import { SearchServiceClient } from '@google-cloud/discoveryengine';
import { Storage } from '@google-cloud/storage';
import * as logger from 'firebase-functions/logger';

const storage = new Storage();

// Configuration constants
const PROJECT_ID = '487213218407';
const LOCATION = 'global';
const DATA_STORE_ID = 'fadebender-knowledge';
const SERVING_CONFIG_ID = 'default_search';

// Client instantiation
const client = new SearchServiceClient();

// Rate limiting: Track requests to stay under quota (10/min until upgrade to 100/min)
let requestCount = 0;
let requestWindowStart = Date.now();
const MAX_REQUESTS_PER_MINUTE = 8; // Stay under 10/min limit with buffer

export interface VertexSearchOptions {
  query: string;
  context?: Record<string, any>;
}

export interface SearchResult {
  title: string;
  snippet: string;
  uri: string;
}

export interface SearchResultsResponse {
  results: SearchResult[];
  totalResults: number;
  query: string;
}

/**
 * Search Vertex AI for relevant documents (NO LLM summary generation)
 * Returns raw search results to stay within free quota limits.
 */
export async function callVertexSearch(options: VertexSearchOptions): Promise<string> {
  const { query } = options;

  const name = client.projectLocationCollectionDataStoreServingConfigPath(
    PROJECT_ID,
    LOCATION,
    'default_collection',
    DATA_STORE_ID,
    SERVING_CONFIG_ID
  );

  logger.info('Calling Vertex AI Search (standard edition - with LLM summaries)', { query, path: name });

  // Rate limiting check
  const now = Date.now();
  const timeElapsed = now - requestWindowStart;

  // Reset counter every minute
  if (timeElapsed >= 60000) {
    requestCount = 0;
    requestWindowStart = now;
  }

  // Check if we're at the limit
  if (requestCount >= MAX_REQUESTS_PER_MINUTE) {
    const waitTime = 60000 - timeElapsed;
    logger.warn('Rate limit approaching, backing off', {
      requestCount,
      maxRequests: MAX_REQUESTS_PER_MINUTE,
      waitTimeMs: waitTime,
    });

    // Return empty result to trigger fallback to local Gemini
    throw new Error(`Rate limit: ${requestCount}/${MAX_REQUESTS_PER_MINUTE} requests used. Try again in ${Math.ceil(waitTime / 1000)}s`);
  }

  requestCount++;
  logger.info('Rate limit status', { requestCount, maxRequests: MAX_REQUESTS_PER_MINUTE });

  try {
    // Standard edition: Search-only mode (no LLM summaries)
    // We'll fetch document content separately and let Python/Gemini generate answers
    const request = {
      servingConfig: name,
      query: query,
      pageSize: 5,
      // NO contentSearchSpec - just basic search
    };

    // search() with autoPaginate: false returns [results]
    const [results] = await client.search(request, { autoPaginate: false });

    logger.info('Vertex AI Search results', {
      hasResults: !!results,
      resultsLength: results ? results.length : 0,
    });

    // Fetch and extract content from documents
    let answer = '';

    if (results && results.length > 0) {
      const documentsWithContent = await Promise.all(
        results.slice(0, 5).map(async (r: any, index: number) => {
          const fields = r.document?.derivedStructData?.fields || {};
          const title = fields.title?.stringValue || r.document?.name || 'Untitled';
          const uri = fields.link?.stringValue || r.document?.name || '';

          // Fetch actual content from gs:// URL
          let content = '';
          if (uri.startsWith('gs://')) {
            try {
              content = await fetchDocumentContent(uri);
              content = extractRelevantText(content, query, 800); // Extract ~800 chars relevant to query
            } catch (error: any) {
              logger.warn('Could not fetch document content', { uri, error: error.message });
            }
          }

          return { index: index + 1, title, uri, content };
        })
      );

      // Format as JSON for Python/Gemini to process
      answer = JSON.stringify({
        query,
        documents: documentsWithContent.map(doc => ({
          title: doc.title,
          content: doc.content,
          source: doc.uri,
        })),
      });

      logger.info('Documents fetched with content', {
        documentCount: documentsWithContent.length,
        totalContentLength: documentsWithContent.reduce((sum, d) => sum + d.content.length, 0),
      });
    } else {
      answer = JSON.stringify({
        query,
        documents: [],
        message: "No relevant documents found in the knowledge base for this query.",
      });
    }

    logger.info('Vertex AI Search complete', {
      resultsCount: results?.length || 0,
      responseLength: answer.length,
    });

    return answer;

  } catch (error: any) {
    logger.error('Vertex AI Search call failed', { error: error.message, query });
    throw new Error(`Vertex AI Search failed: ${error.message}`);
  }
}

/**
 * Fetch document content from Google Cloud Storage
 */
async function fetchDocumentContent(gsUri: string): Promise<string> {
  // Parse gs://bucket/path
  const match = gsUri.match(/^gs:\/\/([^/]+)\/(.+)$/);
  if (!match) {
    throw new Error(`Invalid GCS URI: ${gsUri}`);
  }

  const [, bucket, filePath] = match;
  const file = storage.bucket(bucket).file(filePath);

  const [content] = await file.download();
  return content.toString('utf-8');
}

/**
 * Extract relevant text from HTML content
 * Strips HTML tags and extracts text around query keywords
 */
function extractRelevantText(html: string, query: string, maxLength: number): string {
  // Strip HTML tags but keep text
  let text = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove scripts
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '') // Remove styles
    .replace(/<[^>]+>/g, ' ') // Remove HTML tags
    .replace(/\s+/g, ' ') // Collapse whitespace
    .trim();

  // Find text around query keywords
  const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length > 3);

  if (queryWords.length === 0) {
    // No meaningful keywords, return start of document
    return text.substring(0, maxLength);
  }

  // Find best match section
  const lowerText = text.toLowerCase();
  let bestIndex = -1;
  let bestScore = 0;

  for (const word of queryWords) {
    const index = lowerText.indexOf(word);
    if (index !== -1 && index < bestIndex + 200) {
      bestScore++;
      if (bestIndex === -1) bestIndex = index;
    }
  }

  if (bestIndex === -1) {
    // No matches found, return start
    return text.substring(0, maxLength);
  }

  // Extract context around match
  const start = Math.max(0, bestIndex - 100);
  const end = Math.min(text.length, start + maxLength);

  let excerpt = text.substring(start, end);

  // Clean up partial words at boundaries
  if (start > 0) {
    excerpt = '...' + excerpt.substring(excerpt.indexOf(' ') + 1);
  }
  if (end < text.length) {
    excerpt = excerpt.substring(0, excerpt.lastIndexOf(' ')) + '...';
  }

  return excerpt;
}
