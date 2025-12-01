"""
OpenAI Assistants API RAG Service with File Search

Provides conversational document search using OpenAI's Assistants API.
Features:
- Automatic document chunking and embedding
- Built-in conversational context (threads)
- GPT-4 powered natural language understanding
- Grounding with citations

Cost: ~$5-10/month for typical usage
- Vector storage: $0.10/GB/day
- Retrieval: $0.20/GB
- GPT-4 queries: ~$0.01-0.03 per query
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class AssistantRAGService:
    """OpenAI Assistants API with File Search for conversational document Q&A"""

    def __init__(self, knowledge_dir: str = None):
        """
        Initialize Assistants API RAG service

        Args:
            knowledge_dir: Path to knowledge base files (HTML/MD)
        """
        self.knowledge_dir = knowledge_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            '../knowledge/fadebender'
        )

        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Storage for assistant and vector store IDs
        self.assistant_id = None
        self.vector_store_id = None

        # Conversation threads (user_id -> thread_id)
        self.user_threads: Dict[str, str] = {}

        # Initialize or load assistant
        self._setup_assistant()

    def _setup_assistant(self):
        """Create or load the Fadebender assistant with file search"""
        # Check if we have stored IDs (would be in a config file or DB in production)
        # For now, create new assistant each time server starts

        try:
            # Create vector store for knowledge base
            logger.info("Creating vector store for knowledge base...")
            vector_store = self.client.vector_stores.create(
                name="fadebender-knowledge"
            )
            self.vector_store_id = vector_store.id
            logger.info(f"Created vector store: {self.vector_store_id}")

            # Upload knowledge files
            self._upload_knowledge_files()

            # Create assistant with file search
            logger.info("Creating Fadebender assistant...")
            assistant = self.client.beta.assistants.create(
                name="Fadebender Assistant",
                instructions="""You are an expert audio engineer and Ableton Live instructor helping users with Fadebender, a natural language control system for Ableton Live.

Your role:
- Answer questions about Fadebender features, commands, and usage
- Help users understand available presets and device controls
- Provide clear, actionable guidance for music production tasks
- Always ground your answers in the provided documentation
- Be conversational and remember context from previous questions

When listing presets or devices:
- CRITICAL: Return EVERY SINGLE item from the documentation - do NOT truncate or summarize lists
- If there are 52 presets, list all 52 - never say "here are some examples" or provide partial lists
- Format responses clearly with numbered lists
- Include all preset IDs and names exactly as they appear in the catalog
- If a list is very long, still include every item - users need complete information

Communication style:
- Professional but friendly
- Exhaustive when listing items (never summarize lists)
- Use markdown formatting for clarity
- Cite sources when providing specific technical details""",
                model="gpt-4o",  # More capable, better for complete lists
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            self.assistant_id = assistant.id
            logger.info(f"Created assistant: {self.assistant_id}")

        except Exception as e:
            logger.error(f"Failed to setup assistant: {e}")
            raise

    def _upload_knowledge_files(self):
        """Upload knowledge base files to vector store"""
        knowledge_path = Path(self.knowledge_dir)

        # Find all markdown files (they're more readable than HTML for GPT)
        md_files = list(knowledge_path.glob('*.md'))

        if not md_files:
            logger.warning(f"No markdown files found in {self.knowledge_dir}")
            return

        logger.info(f"Uploading {len(md_files)} knowledge files...")

        # Upload files to OpenAI
        file_streams = []
        for md_file in md_files:
            file_streams.append(open(md_file, "rb"))

        try:
            # Batch upload to vector store
            file_batch = self.client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=self.vector_store_id,
                files=file_streams
            )

            logger.info(f"Uploaded {file_batch.file_counts.completed} files successfully")

        finally:
            # Close all file streams
            for stream in file_streams:
                stream.close()

    def query(
        self,
        user_id: str,
        question: str,
        reset_conversation: bool = False
    ) -> Dict[str, Any]:
        """
        Ask a question with conversational context

        Args:
            user_id: User identifier for maintaining conversation thread
            question: User's question
            reset_conversation: If True, start a new conversation thread

        Returns:
            Dict with answer, sources, and thread_id
        """
        try:
            # Get or create thread for this user
            if reset_conversation or user_id not in self.user_threads:
                thread = self.client.beta.threads.create()
                self.user_threads[user_id] = thread.id
                logger.info(f"Created new thread for user {user_id}: {thread.id}")

            thread_id = self.user_threads[user_id]

            # Add user message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=question
            )

            # Run the assistant
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=self.assistant_id
            )

            # Get the response
            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread_id
                )

                # Get the latest assistant message
                assistant_messages = [
                    msg for msg in messages.data
                    if msg.role == "assistant"
                ]

                if assistant_messages:
                    latest_message = assistant_messages[0]

                    # Extract text content
                    answer = ""
                    for content in latest_message.content:
                        if content.type == "text":
                            answer = content.text.value
                            break

                    # Extract citations/sources
                    sources = self._extract_sources(latest_message)

                    return {
                        "ok": True,
                        "answer": answer,
                        "sources": sources,
                        "thread_id": thread_id,
                        "mode": "openai-assistants"
                    }

            # Handle failed run
            logger.error(f"Assistant run failed with status: {run.status}")
            return {
                "ok": False,
                "error": f"Assistant run failed: {run.status}",
                "thread_id": thread_id
            }

        except Exception as e:
            logger.error(f"Error querying assistant: {e}")
            return {
                "ok": False,
                "error": str(e)
            }

    def _extract_sources(self, message) -> List[Dict[str, str]]:
        """Extract source citations from assistant message"""
        sources = []

        for content in message.content:
            if content.type == "text":
                # Check for annotations (file citations)
                if hasattr(content.text, 'annotations'):
                    for annotation in content.text.annotations:
                        if annotation.type == "file_citation":
                            # Get file citation details
                            file_citation = annotation.file_citation
                            sources.append({
                                "file_id": file_citation.file_id,
                                "quote": getattr(annotation, 'text', ''),
                            })

        return sources

    def reset_conversation(self, user_id: str):
        """Reset conversation for a user (start fresh thread)"""
        if user_id in self.user_threads:
            del self.user_threads[user_id]
            logger.info(f"Reset conversation for user {user_id}")

    def cleanup(self):
        """Cleanup resources (call on shutdown)"""
        try:
            # Delete assistant and vector store
            if self.assistant_id:
                self.client.beta.assistants.delete(self.assistant_id)
                logger.info(f"Deleted assistant {self.assistant_id}")

            if self.vector_store_id:
                self.client.vector_stores.delete(self.vector_store_id)
                logger.info(f"Deleted vector store {self.vector_store_id}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Singleton instance
_assistant_rag = None

def get_assistant_rag() -> AssistantRAGService:
    """Get or create singleton Assistant RAG service"""
    global _assistant_rag
    if _assistant_rag is None:
        _assistant_rag = AssistantRAGService()
    return _assistant_rag
