"""
Tier 2: Semantic Search with Gemini Embeddings + Flash Lite
Fast semantic search for "best for X", "similar to Y", recommendations
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from google.cloud import firestore
import vertexai
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)


class QueryClass(Enum):
    """Query classification for Tier-2 prompt selection"""
    PRESET_COMPARISON = "preset_comparison"
    PARAMETER_EXPLANATION = "parameter_explanation"
    RECOMMENDATION = "recommendation"
    GENERAL_SEMANTIC = "general_semantic"


class SemanticSearchService:
    """Fast semantic search using Firestore vector similarity + Gemini Flash"""

    def __init__(self):
        project_id = os.getenv('FIRESTORE_PROJECT_ID', 'fadebender')
        database_id = os.getenv('FIRESTORE_DATABASE_ID', 'dev-display-value')

        self.db = firestore.Client(
            project=project_id,
            database=database_id
        )

        # Initialize Vertex AI
        vertexai.init(project=project_id)

        # Embedding model (text-embedding-004 is latest and fastest)
        self.embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")

        # Load model from app_config.json
        model_name = self._load_model_from_config()
        self.flash_model = GenerativeModel(model_name)

        # Load Tier-2 prompts and config
        self.prompts = self._load_tier2_prompts()
        self.tier2_config = self._load_tier2_config()

        # Log version info
        prompt_version = self.tier2_config.get('version', 'unknown')
        prompt_date = self.tier2_config.get('last_updated', 'unknown')
        logger.info(f"[SemanticSearch] Initialized with project={project_id}, database={database_id}, model={model_name}")
        logger.info(f"[SemanticSearch] Prompts v{prompt_version} (updated: {prompt_date})")

    def _load_model_from_config(self) -> str:
        """Load help_assistant model from app_config.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'configs', 'app_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                model = config.get('models', {}).get('help_assistant', 'gemini-2.5-flash-lite')
                logger.info(f"[SemanticSearch] Loaded model from config: {model}")
                return model
        except Exception as e:
            logger.warning(f"[SemanticSearch] Could not load config, using default: {e}")
            return 'gemini-2.5-flash-lite'

    def _load_tier2_config(self) -> Dict[str, Any]:
        """Load Tier-2 configuration from prompts/tier2/config.json"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'tier2', 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"[SemanticSearch] Loaded Tier-2 config v{config.get('version', '?')}")
                return config
        except Exception as e:
            logger.warning(f"[SemanticSearch] Could not load Tier-2 config: {e}")
            return {
                "classifier": {
                    "PRESET_COMPARISON": ["compare", "vs", "versus", "difference"],
                    "RECOMMENDATION": ["best for", "recommend", "suggest", "good for"],
                    "GENERAL_SEMANTIC": []
                },
                "confidence_threshold": 0.60,
                "handoff_keyword": "HANDOFF_TIER3"
            }

    def _load_tier2_prompts(self) -> Dict[str, str]:
        """Load Tier-2 prompt templates from prompts/tier2/"""
        prompts = {}
        try:
            prompts_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts', 'tier2')

            # Load system prompt
            system_path = os.path.join(prompts_dir, 'system_prompt.md')
            with open(system_path, 'r') as f:
                prompts['system'] = f.read()

            # Load templates
            templates_dir = os.path.join(prompts_dir, 'templates')
            for template_file in ['preset_comparison.md', 'parameter_explanation.md',
                                 'recommendation.md', 'general_semantic.md']:
                template_path = os.path.join(templates_dir, template_file)
                template_key = template_file.replace('.md', '')
                with open(template_path, 'r') as f:
                    prompts[template_key] = f.read()

            logger.info(f"[SemanticSearch] Loaded {len(prompts)} Tier-2 prompts")
            return prompts
        except Exception as e:
            logger.warning(f"[SemanticSearch] Could not load Tier-2 prompts: {e}")
            return {}

    def _classify_query(self, query: str) -> Tuple[QueryClass, float]:
        """Classify query into QueryClass using patterns from config"""
        query_lower = query.lower()
        classifier = self.tier2_config.get('classifier', {})

        # Check each query class in priority order
        for class_name, patterns in classifier.items():
            if class_name == "GENERAL_SEMANTIC":
                continue  # This is the fallback

            for pattern in patterns:
                if re.search(pattern, query_lower):
                    query_class = QueryClass[class_name]
                    confidence = 0.8  # High confidence for pattern match
                    logger.info(f"[SemanticSearch] Classified as {query_class.value} (confidence: {confidence})")
                    return query_class, confidence

        # Fallback to general semantic
        logger.info(f"[SemanticSearch] Classified as general_semantic (default)")
        return QueryClass.GENERAL_SEMANTIC, 0.6

    def search_similar_presets(
        self,
        query: str,
        device_name: Optional[str] = None,
        top_k: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Search for presets semantically similar to query

        Args:
            query: User's natural language query
            device_name: Optional device filter (reverb, delay, etc)
            top_k: Number of similar presets to return

        Returns:
            Dict with similar presets and generated response
        """
        try:
            # Step 1: Generate query embedding
            logger.info(f"[SemanticSearch] Generating embedding for: {query}")
            embeddings = self.embedding_model.get_embeddings([query])
            query_embedding = embeddings[0].values

            # Step 2: Get all presets with embeddings
            # For now, we'll do in-memory similarity since we have <200 presets
            # In production, use Firestore vector search when available
            presets = self._get_presets_with_embeddings(device_name)

            if not presets:
                logger.warning("[SemanticSearch] No presets with embeddings found")
                return None

            # Step 3: Calculate cosine similarity
            similar_presets = self._calculate_similarity(query_embedding, presets, top_k)

            # Step 4: Generate natural language response with Flash Lite
            response_text = self._generate_response(query, similar_presets)

            # Check if model requested handoff to Tier-3
            if response_text is None:
                logger.info(f"[SemanticSearch] HANDOFF_TIER3 triggered, escalating to RAG")
                return None  # Signal to escalate to Tier-3

            result = {
                'similar_presets': similar_presets,
                'response': response_text,
                'count': len(similar_presets)
            }

            logger.info(f"[SemanticSearch] Found {len(similar_presets)} similar presets")
            return result

        except Exception as e:
            logger.error(f"[SemanticSearch] Error in semantic search: {e}")
            return None

    def _get_presets_with_embeddings(self, device_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all presets that have embeddings stored"""
        try:
            presets_ref = self.db.collection('presets').stream()

            presets = []
            for preset in presets_ref:
                doc_id = preset.id
                data = preset.to_dict()

                # Filter by device if specified
                if device_name:
                    device_lower = device_name.lower()
                    if not doc_id.startswith(f'{device_lower}_'):
                        continue

                # Check if preset has embedding
                if 'embedding' in data and data['embedding']:
                    # Extract preset name from ID
                    preset_name = doc_id.split('_', 1)[1] if '_' in doc_id else doc_id
                    preset_name = ' '.join(word.capitalize() for word in preset_name.replace('_', ' ').split())

                    presets.append({
                        'id': doc_id,
                        'name': preset_name,
                        'device': doc_id.split('_')[0] if '_' in doc_id else 'unknown',
                        'embedding': data['embedding'],
                        'category': data.get('category', 'Unknown'),
                        'description': data.get('description', ''),
                        'parameter_values': data.get('parameter_display_values', {})
                    })

            logger.info(f"[SemanticSearch] Loaded {len(presets)} presets with embeddings")
            return presets

        except Exception as e:
            logger.error(f"[SemanticSearch] Error loading presets: {e}")
            return []

    def _calculate_similarity(
        self,
        query_embedding: List[float],
        presets: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Calculate cosine similarity between query and preset embeddings"""
        import numpy as np

        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)

        similarities = []
        for preset in presets:
            preset_vec = np.array(preset['embedding'])
            preset_norm = np.linalg.norm(preset_vec)

            # Cosine similarity
            if query_norm > 0 and preset_norm > 0:
                similarity = np.dot(query_vec, preset_vec) / (query_norm * preset_norm)
                similarities.append({
                    'preset': preset,
                    'similarity': float(similarity)
                })

        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        results = []
        for item in similarities[:top_k]:
            preset = item['preset']
            results.append({
                'id': preset['id'],
                'name': preset['name'],
                'device': preset['device'],
                'category': preset['category'],
                'similarity': item['similarity'],
                'parameters': preset['parameter_values']
            })

        return results

    def _generate_response(self, query: str, similar_presets: List[Dict[str, Any]]) -> str:
        """Generate natural language response using template-based prompts"""
        try:
            # Classify query to select appropriate template
            query_class, confidence = self._classify_query(query)

            # Build preset context from similar_presets
            preset_context = self._build_preset_context(similar_presets, query_class)

            # Select appropriate template
            template_key = query_class.value  # e.g., "preset_comparison"
            query_template = self.prompts.get(template_key, self.prompts.get('general_semantic', ''))
            system_prompt = self.prompts.get('system', '')

            # Assemble full prompt
            full_prompt = f"""{system_prompt}

{query_template}

--- BEGIN RETRIEVED CONTEXT ---
{preset_context}
--- END RETRIEVED CONTEXT ---

--- USER QUESTION ---
{query}

Reminder: If context insufficient, output {self.tier2_config.get('handoff_keyword', 'HANDOFF_TIER3')}."""

            logger.info(f"[SemanticSearch] Using template: {template_key}, confidence: {confidence}")

            # Generate response
            response = self.flash_model.generate_content(
                full_prompt,
                generation_config={
                    'max_output_tokens': 400,
                    'temperature': 0.7,
                }
            )

            response_text = response.text.strip()

            # Check for HANDOFF_TIER3
            handoff_keyword = self.tier2_config.get('handoff_keyword', 'HANDOFF_TIER3')
            if handoff_keyword in response_text:
                logger.info(f"[SemanticSearch] Model requested handoff to Tier-3")
                # Return None to signal escalation needed
                return None

            return response_text

        except Exception as e:
            logger.error(f"[SemanticSearch] Error generating response: {e}")
            # Fallback to simple list
            preset_list = ", ".join([p['name'] for p in similar_presets[:3]])
            return f"Based on your query, I'd recommend these presets: {preset_list}"

    def _build_preset_context(self, similar_presets: List[Dict[str, Any]], query_class: QueryClass) -> str:
        """Build formatted preset context based on query class"""
        context_lines = []

        for i, preset in enumerate(similar_presets[:5], 1):
            name = preset.get('name', '?')
            device = preset.get('device', '?')
            category = preset.get('category', 'Unknown')
            similarity = preset.get('similarity', 0.0)
            params = preset.get('parameters', {})

            # Format based on query class
            if query_class == QueryClass.PRESET_COMPARISON:
                # Include detailed parameter info for comparisons
                param_str = ", ".join([f"{k}: {v}" for k, v in list(params.items())[:6]])
                context_lines.append(f"{i}. {name} ({device})")
                context_lines.append(f"   Category: {category}")
                context_lines.append(f"   Key parameters: {param_str}")
                context_lines.append(f"   Similarity score: {similarity:.3f}\n")
            elif query_class == QueryClass.PARAMETER_EXPLANATION:
                # Focus on parameter values
                context_lines.append(f"{i}. {name} ({device})")
                context_lines.append(f"   Parameters: {json.dumps(params, indent=6)}\n")
            else:
                # Simpler format for recommendations
                context_lines.append(f"- {name} ({device}, category: {category}, similarity: {similarity:.3f})")

        return "\n".join(context_lines)

    def find_preset_by_description(
        self,
        description: str,
        device_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find preset matching a description (e.g., 'warm reverb', 'short delay')"""
        return self.search_similar_presets(description, device_name, top_k=3)


# Singleton instance
_semantic_search_service = None

def get_semantic_search_service() -> SemanticSearchService:
    """Get or create SemanticSearchService singleton"""
    global _semantic_search_service
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    return _semantic_search_service
