"""LLM-powered help response generator for Fadebender audio assistant.

Uses Gemini 2.5 Flash Lite to generate concise, formatted help responses
from knowledge base snippets.
"""
from __future__ import annotations

import os
import sys
import pathlib
from typing import Dict, List, Tuple, Any

# Import Vertex AI
try:
    import vertexai  # type: ignore
    from vertexai.generative_models import GenerativeModel  # type: ignore
except ImportError:
    vertexai = None  # type: ignore
    GenerativeModel = None  # type: ignore


# Vertex AI initialization (done once)
_vertex_initialized = False


def _init_vertex() -> None:
    """Initialize Vertex AI once."""
    global _vertex_initialized
    if _vertex_initialized or vertexai is None:
        return

    # Import from nlp-service config
    nlp_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "nlp-service"
    if nlp_dir.exists() and str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))

    try:
        from config.llm_config import get_llm_project_id  # type: ignore

        project = get_llm_project_id()
        location = os.getenv("GCP_REGION", "us-central1")
        vertexai.init(project=project, location=location)  # type: ignore
        _vertex_initialized = True
    except Exception:
        pass


def generate_help_response(
    query: str,
    knowledge_snippets: List[Tuple[str, str, str]],
    suggested_intents: List[str],
) -> str:
    """Generate a concise, well-formatted help response using Gemini 2.5 Flash Lite.

    Args:
        query: User's help question
        knowledge_snippets: List of (source, title, body) tuples from knowledge base
        suggested_intents: List of suggested command examples

    Returns:
        Markdown-formatted help response
    """
    if GenerativeModel is None or not knowledge_snippets:
        return _fallback_response(query, knowledge_snippets, suggested_intents)

    _init_vertex()

    try:
        # Get model name from config
        try:
            from server.config.app_config import get_model_for_operation

            model_name = get_model_for_operation("help_assistant")
        except Exception:
            model_name = os.getenv("VERTEX_MODEL") or "gemini-2.5-flash-lite"

        # Build context from knowledge snippets (limit total length)
        context_parts = []
        total_chars = 0
        max_chars = 4000  # Limit context to stay within token limits

        for source, title, body in knowledge_snippets:
            # Truncate long sections
            truncated_body = body[:800] if len(body) > 800 else body
            snippet = f"**{title}** (from {source}):\n{truncated_body}"

            if total_chars + len(snippet) > max_chars:
                break

            context_parts.append(snippet)
            total_chars += len(snippet)

        context = "\n\n---\n\n".join(context_parts)

        # Build prompt
        prompt = f"""You are an expert audio engineering assistant for Fadebender, a text-based chat interface for controlling Ableton Live.

**User Question**: {query}

**Knowledge Base Context**:
{context}

**Task**: Generate a concise, helpful answer (2-4 paragraphs max) using the knowledge base context. Format your response in markdown with:

1. A brief, direct answer to the question
2. Key practical advice or techniques (if applicable)
3. Reference specific Fadebender text commands when relevant (in backticks)

**Important**:
- Fadebender uses TEXT commands (e.g., `set track 1 volume to -6 dB`), NOT voice control
- Be concise but informative (max 200 words)
- Use markdown formatting (bold for emphasis, bullet lists for steps)
- Show exact command syntax in backticks when suggesting Fadebender commands
- Focus on practical, actionable information
- Don't repeat the question
- If the knowledge base doesn't cover the topic well, say so briefly and suggest related topics

**Response**:"""

        model = GenerativeModel(model_name)
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,  # Lower temperature for more focused responses
                "top_p": 0.9,
                "max_output_tokens": 500,  # Keep responses concise
            },
        )

        if response and response.text:
            return response.text.strip()

    except Exception as e:
        print(f"Error generating help response: {e}")

    # Fallback to simple response
    return _fallback_response(query, knowledge_snippets, suggested_intents)


def _fallback_response(
    query: str,
    knowledge_snippets: List[Tuple[str, str, str]],
    suggested_intents: List[str],
) -> str:
    """Generate a simple fallback response without LLM."""
    if not knowledge_snippets:
        return f"I don't have specific information about '{query}' in the knowledge base. Try asking about audio engineering concepts, Ableton Live features, or Fadebender commands."

    # Build simple response from first snippet
    source, title, body = knowledge_snippets[0]

    # Truncate body if too long
    if len(body) > 400:
        body = body[:400] + "..."

    response = f"**{title}**\n\n{body}"

    if len(knowledge_snippets) > 1:
        response += f"\n\n*Found {len(knowledge_snippets)} related topics in the knowledge base.*"

    return response
