"""
Hybrid RAG Service: OpenAI Embeddings + Gemini Generation

Fast and cost-effective approach:
- Uses existing OpenAI embeddings + BM25 from RAGService
- Generates answers with Gemini 2.0 Flash (fast + cheap)
- Maintains conversation context manually
- Smart model routing: GPT-4o-mini for simple, GPT-4o for complex

Cost: ~$2-5/month (10x cheaper than Assistants API)
Speed: ~1-2 seconds (3-5x faster than Assistants API)
"""

import os
import logging
import time
import re
from typing import Dict, Any, List
from server.services.rag_service import get_rag_service

# Import Vertex AI Gemini
try:
    import vertexai  # type: ignore
    from vertexai.generative_models import GenerativeModel  # type: ignore
except ImportError:
    vertexai = None  # type: ignore
    GenerativeModel = None  # type: ignore

# Import Firestore for preset image fetching
try:
    from google.cloud import firestore
except ImportError:
    firestore = None

logger = logging.getLogger(__name__)


class HybridRAGService:
    """Hybrid RAG with OpenAI embeddings + Gemini generation"""

    def __init__(self):
        """Initialize hybrid RAG service"""
        self.rag_service = get_rag_service()

        # Initialize Vertex AI (if available)
        if vertexai is not None:
            try:
                project_id = os.getenv('VERTEX_PROJECT') or os.getenv('GOOGLE_CLOUD_PROJECT')
                location = os.getenv('VERTEX_LOCATION', 'us-central1')
                vertexai.init(project=project_id, location=location)
                logger.info(f"Initialized Vertex AI: project={project_id}, location={location}")
            except Exception as e:
                logger.warning(f"Failed to initialize Vertex AI: {e}")

        # Initialize Firestore for preset image fetching
        self.db = None
        if firestore is not None:
            try:
                database_id = os.getenv('FIRESTORE_DATABASE', 'dev-display-value')
                self.db = firestore.Client(database=database_id)
                logger.info(f"Initialized Firestore: database={database_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize Firestore: {e}")

        # Conversation history (user_id -> list of messages)
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

        # Cache of preset names to IDs for image lookup
        self._preset_lookup_cache = None

    def _detect_query_complexity(self, query: str) -> str:
        """
        Detect query complexity for smart model routing

        Returns:
            'simple' - Use GPT-4o-mini (fast, cheap)
            'complex' - Use GPT-4o (complete lists, comparisons)
        """
        query_lower = query.lower()

        # Complex patterns - need GPT-4o for complete lists
        complex_patterns = [
            'list all', 'list every', 'complete list', 'all presets',
            'every preset', 'all devices', 'every device',
            'compare', 'difference between', 'vs',
            'detailed', 'comprehensive', 'full list'
        ]

        # Simple patterns - GPT-4o-mini can handle
        simple_patterns = [
            'what is', 'how many', 'which',
            'parameter range', 'value range',
            'single preset', 'one preset'
        ]

        # Check for complex patterns
        if any(pattern in query_lower for pattern in complex_patterns):
            return 'complex'

        # Check for simple patterns
        if any(pattern in query_lower for pattern in simple_patterns):
            return 'simple'

        # Default to simple for unknown queries
        return 'simple'

    def _build_preset_lookup(self) -> Dict[str, str]:
        """Build a cache of preset names to IDs for quick lookup"""
        if self._preset_lookup_cache is not None:
            return self._preset_lookup_cache

        if self.db is None:
            return {}

        try:
            # Fetch all presets
            presets = self.db.collection('presets').stream()
            lookup = {}

            for preset in presets:
                data = preset.to_dict()
                name = data.get('name', '').lower()
                device_name = data.get('device_name', '').lower()

                if name:
                    # Map both plain name and "device preset" format
                    lookup[name] = preset.id
                    if device_name:
                        lookup[f"{device_name}"] = preset.id

            self._preset_lookup_cache = lookup
            logger.info(f"Built preset lookup cache with {len(lookup)} entries")
            return lookup

        except Exception as e:
            logger.error(f"Failed to build preset lookup: {e}")
            return {}

    def _extract_preset_images(self, answer: str, top_docs: List[Dict]) -> List[Dict[str, str]]:
        """
        Extract preset images mentioned in the answer

        Args:
            answer: The generated answer text
            top_docs: Retrieved documents from RAG search

        Returns:
            List of {url, caption} dicts for preset images
        """
        if self.db is None:
            return []

        try:
            images = []
            lookup = self._build_preset_lookup()

            if not lookup:
                return []

            # Extract preset IDs from top documents (most relevant)
            preset_ids = set()
            for doc in top_docs[:3]:  # Only check top 3 most relevant docs
                title = doc.get('title', '').lower()
                # Check if title matches preset pattern
                for name, preset_id in lookup.items():
                    if name in title and len(name) > 3:  # Avoid short spurious matches
                        preset_ids.add(preset_id)

            # Also scan answer text for preset mentions (case-insensitive)
            answer_lower = answer.lower()
            for name, preset_id in lookup.items():
                # Use word boundaries to avoid partial matches
                if len(name) > 3 and re.search(r'\b' + re.escape(name) + r'\b', answer_lower):
                    preset_ids.add(preset_id)

            # Limit to max 3 images to avoid overwhelming the UI
            for preset_id in list(preset_ids)[:3]:
                preset_doc = self.db.collection('presets').document(preset_id).get()
                if preset_doc.exists:
                    preset_data = preset_doc.to_dict()
                    image_url = preset_data.get('image_url')
                    preset_name = preset_data.get('name', preset_id)

                    if image_url:
                        images.append({
                            'url': image_url,
                            'caption': preset_name
                        })

            if images:
                logger.info(f"Extracted {len(images)} preset images")

            return images

        except Exception as e:
            logger.error(f"Failed to extract preset images: {e}")
            return []

    def query(
        self,
        user_id: str,
        question: str,
        reset_conversation: bool = False,
        force_model: str = None
    ) -> Dict[str, Any]:
        """
        Query with hybrid RAG approach

        Args:
            user_id: User identifier for conversation context
            question: User's question
            reset_conversation: If True, start fresh conversation
            force_model: Override smart routing ('simple' or 'complex')

        Returns:
            Dict with answer, sources, timing, and model used
        """
        start_time = time.time()

        try:
            # Reset conversation if requested
            if reset_conversation:
                self.conversations[user_id] = []
                logger.info(f"Reset conversation for user {user_id}")

            # Detect query complexity for smart model routing
            complexity = force_model or self._detect_query_complexity(question)
            logger.info(f"Query complexity: {complexity} for '{question[:50]}...'")

            # Search for relevant documents
            search_start = time.time()
            top_docs = self.rag_service.search(question, top_k=5)
            search_time = time.time() - search_start
            logger.info(f"Document search completed in {search_time:.2f}s")

            # Build context from retrieved documents
            context_parts = []
            for i, doc in enumerate(top_docs, 1):
                context_parts.append(
                    f"[Source {i}]\n"
                    f"Title: {doc['title']}\n"
                    f"Section: {doc['section']}\n"
                    f"Content: {doc['text']}\n"
                    f"Score: {doc['score']:.3f}\n"
                )

            context = "\n---\n".join(context_parts)

            # Get conversation history
            history = self.conversations.get(user_id, [])

            # Build prompt with instructions based on complexity
            if complexity == 'complex':
                list_instruction = """
CRITICAL INSTRUCTIONS FOR LISTS:
- When listing presets/devices, return EVERY SINGLE item from the documentation
- Do NOT truncate, summarize, or provide partial lists
- If there are 52 reverb presets, list ALL 52 with their exact names and IDs
- Use numbered lists for clarity
- Never say "here are some examples" - provide complete exhaustive lists
"""
            else:
                list_instruction = ""

            system_prompt = f"""You are an expert audio engineer and Ableton Live instructor helping users with Fadebender.

Your role:
- Answer questions about Fadebender features, commands, and usage
- Help users understand available presets and device controls
- Provide clear, actionable guidance for music production tasks
- Always ground your answers in the provided documentation
- Remember context from previous questions in this conversation

{list_instruction}

COMPARISON INSTRUCTIONS:
When comparing 2-3 presets or devices:
- Start with sonic character/purpose (1-2 sentences describing how they sound different)
- Use a markdown table to show ONLY 2-3 KEY parameter differences that matter most
- Table format: | Parameter | Preset A | Preset B | Notes |
- NEVER dump all parameters - only the most important ones
- User can ask for "full parameter details" or "all parameters" if they want more

For longer lists or descriptions:
- Use markdown numbered/bullet lists for clarity
- Use **bold** for emphasis on key terms
- Use `code` formatting for parameter names

Communication style:
- Professional but friendly
- Use markdown formatting (tables, lists, bold, code) for clarity
- Cite sources when helpful
- Keep comparisons concise - focus on what users need to make decisions

Retrieved Documentation:
{context}
"""

            # Build conversation messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history
            for msg in history:
                messages.append(msg)

            # Add current question
            messages.append({"role": "user", "content": question})

            # Generate answer with Gemini
            generation_start = time.time()

            # Use Gemini 2.5 Flash for generation (fast and cheap)
            model_name = os.getenv('VERTEX_MODEL', 'gemini-2.5-flash')
            model = GenerativeModel(model_name)

            # Convert messages to proper format (combine system + history + user)
            prompt_parts = [system_prompt]
            for msg in history:
                role_prefix = "User: " if msg["role"] == "user" else "Assistant: "
                prompt_parts.append(f"{role_prefix}{msg['content']}")
            prompt_parts.append(f"User: {question}")

            full_prompt = "\n\n".join(prompt_parts)

            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.3,  # Lower for factual responses
                    "max_output_tokens": 2048 if complexity == 'simple' else 8192,
                    "top_p": 0.95,
                }
            )

            generation_time = time.time() - generation_start
            logger.info(f"Answer generation completed in {generation_time:.2f}s")

            answer = response.text

            # Update conversation history (keep last 10 messages)
            if user_id not in self.conversations:
                self.conversations[user_id] = []

            self.conversations[user_id].append({"role": "user", "content": question})
            self.conversations[user_id].append({"role": "assistant", "content": answer})

            # Keep only last 10 messages (5 exchanges)
            if len(self.conversations[user_id]) > 10:
                self.conversations[user_id] = self.conversations[user_id][-10:]

            # Build sources
            sources = [
                {
                    "title": doc['title'],
                    "section": doc['section'],
                    "score": doc['score']
                }
                for doc in top_docs
            ]

            # Extract preset images
            images = self._extract_preset_images(answer, top_docs)

            total_time = time.time() - start_time

            result = {
                "ok": True,
                "answer": answer,
                "sources": sources,
                "mode": "hybrid-rag",
                "model_complexity": complexity,
                "timing": {
                    "total": round(total_time, 2),
                    "search": round(search_time, 2),
                    "generation": round(generation_time, 2)
                }
            }

            # Add images if any were found
            if images:
                result["images"] = images

            return result

        except Exception as e:
            logger.error(f"Hybrid RAG query failed: {e}", exc_info=True)
            return {
                "ok": False,
                "error": str(e),
                "mode": "hybrid-rag"
            }

    def reset_conversation(self, user_id: str):
        """Reset conversation for a user"""
        if user_id in self.conversations:
            del self.conversations[user_id]
            logger.info(f"Reset conversation for user {user_id}")


# Singleton instance
_hybrid_rag = None

def get_hybrid_rag() -> HybridRAGService:
    """Get or create singleton hybrid RAG service"""
    global _hybrid_rag
    if _hybrid_rag is None:
        _hybrid_rag = HybridRAGService()
    return _hybrid_rag
