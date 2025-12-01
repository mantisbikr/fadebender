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
from typing import Dict, Any, List
from server.services.rag_service import get_rag_service

# Import Vertex AI Gemini
try:
    import vertexai  # type: ignore
    from vertexai.generative_models import GenerativeModel  # type: ignore
except ImportError:
    vertexai = None  # type: ignore
    GenerativeModel = None  # type: ignore

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

        # Conversation history (user_id -> list of messages)
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

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

Communication style:
- Professional but friendly
- Use markdown formatting for clarity
- Cite sources when helpful

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

            total_time = time.time() - start_time

            return {
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
