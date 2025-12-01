"""
OpenAI Embeddings + BM25 Hybrid RAG Service

Uses:
- OpenAI text-embedding-3-small for semantic search
- BM25 for keyword matching
- FAISS for fast vector similarity
- Gemini 2.0 Flash for answer generation
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
from bs4 import BeautifulSoup
import numpy as np
from rank_bm25 import BM25Okapi
import faiss
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class RAGService:
    """Hybrid RAG with OpenAI embeddings + BM25 keyword search"""

    def __init__(self, knowledge_dir: str = None, cache_dir: str = None):
        """
        Initialize RAG service

        Args:
            knowledge_dir: Path to knowledge base HTML files
            cache_dir: Path to cache embeddings (avoids regenerating)
        """
        self.knowledge_dir = knowledge_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            '../knowledge/fadebender'
        )
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            '.rag_cache'
        )

        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Storage for documents and indexes
        self.documents: List[Dict[str, Any]] = []
        self.bm25_index = None
        self.faiss_index = None
        self.embeddings = None

        # Load or build indexes
        self._load_or_build_indexes()

    def _load_or_build_indexes(self):
        """Load cached indexes or build from scratch"""
        cache_file = os.path.join(self.cache_dir, 'rag_cache.pkl')

        if os.path.exists(cache_file):
            logger.info("Loading RAG indexes from cache...")
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.documents = cache_data['documents']
                    self.bm25_index = cache_data['bm25_index']
                    self.embeddings = cache_data['embeddings']

                    # Rebuild FAISS index (can't pickle FAISS objects directly)
                    dimension = self.embeddings.shape[1]
                    self.faiss_index = faiss.IndexFlatL2(dimension)
                    self.faiss_index.add(self.embeddings)

                logger.info(f"Loaded {len(self.documents)} documents from cache")
                return
            except Exception as e:
                logger.warning(f"Cache load failed: {e}, rebuilding indexes...")

        logger.info("Building RAG indexes from knowledge base...")
        self._build_indexes()
        self._save_cache(cache_file)

    def _build_indexes(self):
        """Build BM25 and embedding indexes from HTML files"""
        # Load all HTML documents
        self.documents = self._load_documents()

        if not self.documents:
            raise ValueError(f"No documents found in {self.knowledge_dir}")

        logger.info(f"Loaded {len(self.documents)} document chunks")

        # Build BM25 index for keyword search
        tokenized_docs = [doc['tokens'] for doc in self.documents]
        self.bm25_index = BM25Okapi(tokenized_docs)
        logger.info("Built BM25 keyword index")

        # Generate embeddings for semantic search
        texts = [doc['text'] for doc in self.documents]
        self.embeddings = self._generate_embeddings(texts)
        logger.info(f"Generated {len(self.embeddings)} embeddings")

        # Build FAISS index for fast similarity search
        dimension = self.embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatL2(dimension)
        self.faiss_index.add(self.embeddings)
        logger.info("Built FAISS semantic index")

    def _load_documents(self) -> List[Dict[str, Any]]:
        """Load and chunk HTML documents from knowledge base"""
        documents = []
        knowledge_path = Path(self.knowledge_dir)

        # Process all HTML files
        for html_file in knowledge_path.glob('**/*.html'):
            try:
                chunks = self._chunk_html_file(html_file)
                documents.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to process {html_file}: {e}")

        return documents

    def _chunk_html_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Chunk HTML file into manageable pieces

        Strategy:
        - Split by <h2> sections (main topics)
        - Keep chunks around 500-800 tokens
        - Preserve document hierarchy
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'lxml')
        chunks = []

        # Get document title
        title = soup.find('title')
        doc_title = title.get_text() if title else file_path.stem

        # Split by h2 sections
        sections = soup.find_all(['h2', 'h3'])

        if not sections:
            # No sections, treat whole document as one chunk
            text = soup.get_text(separator=' ', strip=True)
            if text:
                chunks.append({
                    'text': text[:2000],  # Limit to 2000 chars
                    'tokens': text.lower().split(),
                    'source': str(file_path),
                    'title': doc_title,
                    'section': ''
                })
        else:
            # Process each section
            for section in sections:
                section_title = section.get_text(strip=True)

                # Get content until next section
                content_parts = []
                for sibling in section.find_next_siblings():
                    if sibling.name in ['h2', 'h3']:
                        break
                    text = sibling.get_text(separator=' ', strip=True)
                    if text:
                        content_parts.append(text)

                if content_parts:
                    full_text = f"{section_title}\n\n" + "\n".join(content_parts)

                    # Split into smaller chunks if too large
                    if len(full_text) > 1500:
                        # Split into ~800 char chunks
                        for i in range(0, len(full_text), 800):
                            chunk_text = full_text[i:i+1200]
                            chunks.append({
                                'text': chunk_text,
                                'tokens': chunk_text.lower().split(),
                                'source': str(file_path),
                                'title': doc_title,
                                'section': section_title
                            })
                    else:
                        chunks.append({
                            'text': full_text,
                            'tokens': full_text.lower().split(),
                            'source': str(file_path),
                            'title': doc_title,
                            'section': section_title
                        })

        return chunks

    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI text-embedding-3-small"""
        embeddings = []
        batch_size = 100  # Process in batches to avoid rate limits

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            logger.info(f"Generating embeddings {i+1}-{min(i+batch_size, len(texts))} of {len(texts)}")

            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
                dimensions=512  # Smaller dimension = faster + cheaper
            )

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

        return np.array(embeddings, dtype='float32')

    def _save_cache(self, cache_file: str):
        """Save indexes to cache file"""
        cache_data = {
            'documents': self.documents,
            'bm25_index': self.bm25_index,
            'embeddings': self.embeddings
        }

        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)

        logger.info(f"Saved RAG cache to {cache_file}")

    def search(self, query: str, top_k: int = 5, bm25_weight: float = 0.3) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 + semantic search

        Args:
            query: Search query
            top_k: Number of results to return
            bm25_weight: Weight for BM25 scores (0-1, rest goes to semantic)

        Returns:
            List of top-k documents with scores
        """
        # Tokenize query for BM25
        query_tokens = query.lower().split()

        # BM25 keyword search
        bm25_scores = self.bm25_index.get_scores(query_tokens)

        # Normalize BM25 scores to 0-1
        if bm25_scores.max() > 0:
            bm25_scores = bm25_scores / bm25_scores.max()

        # Semantic search with embeddings
        query_embedding = self._generate_embeddings([query])[0].reshape(1, -1)
        distances, indices = self.faiss_index.search(query_embedding, len(self.documents))

        # Convert distances to similarity scores (lower distance = higher similarity)
        semantic_scores = 1 / (1 + distances[0])  # Convert to 0-1 range

        # Normalize semantic scores
        if semantic_scores.max() > 0:
            semantic_scores = semantic_scores / semantic_scores.max()

        # Combine scores
        combined_scores = (bm25_weight * bm25_scores) + ((1 - bm25_weight) * semantic_scores)

        # Get top-k results
        top_indices = np.argsort(combined_scores)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            doc = self.documents[idx].copy()
            doc['score'] = float(combined_scores[idx])
            doc['bm25_score'] = float(bm25_scores[idx])
            doc['semantic_score'] = float(semantic_scores[idx])
            results.append(doc)

        return results

    def rebuild_index(self):
        """Force rebuild of all indexes (useful after adding new documents)"""
        logger.info("Rebuilding RAG indexes...")
        self._build_indexes()
        cache_file = os.path.join(self.cache_dir, 'rag_cache.pkl')
        self._save_cache(cache_file)
        logger.info("Index rebuild complete")


# Singleton instance
_rag_service = None

def get_rag_service() -> RAGService:
    """Get or create singleton RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
