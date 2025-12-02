"""
Smart routing for help queries
Routes to Firestore, vector search, or RAG based on query type
"""

import re
import time
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of help queries with different routing strategies"""
    FACTUAL_COUNT = "factual_count"  # "how many X presets?"
    FACTUAL_LIST = "factual_list"    # "list all X presets"
    FACTUAL_PARAMS = "factual_params"  # "what parameters does X have?"
    PARAMETER_SEARCH = "parameter_search"  # "presets with decay < 1s"
    SEMANTIC = "semantic"  # "best for vocals", "recommend for"
    COMPARISON = "comparison"  # "compare X and Y"
    WORKFLOW = "workflow"  # "how do I...", command syntax
    COMPLEX = "complex"  # Requires full RAG


class HelpRouter:
    """Routes help queries to appropriate backend"""

    # Device name patterns (only learned devices)
    DEVICES = ['reverb', 'delay', 'compressor', 'amp']

    # Pattern matching for query classification
    COUNT_PATTERNS = [
        r'how many (\w+) presets?.*',  # Matches "how many reverb presets are there?"
        r'count of (\w+) presets?',
        r'number of (\w+) presets?',
    ]

    LIST_PATTERNS = [
        r'list (all |every )?(\w+) presets?.*',  # "list reverb presets" or "list all reverb presets"
        r'show (all|every) (\w+) presets?.*',
        r'what (\w+) presets (are|do) (available|there|exist|we have).*',
        r'give me (all|every) (\w+) presets?.*',
    ]

    PARAM_PATTERNS = [
        r'what parameters? (can|do) (\w+) (have|control)',  # "what parameters can reverb have"
        r'what (\w+) parameters (can|do) (I|you|we) control',  # "what compressor parameters can I control"
        r'what controls? (on|for) (\w+)',  # "what controls on reverb"
        r'(\w+) parameters',  # "reverb parameters"
    ]

    PARAM_SEARCH_PATTERNS = [
        r'(\w+) presets? with (\w+) (less|greater|under|over|below|above) than (\d+\.?\d*)',
        r'(\w+) with (\w+) < (\d+\.?\d*)',
        r'(\w+) where (\w+) > (\d+\.?\d*)',
        r'find (\w+) presets? .*? (less|greater|under|over) (\d+\.?\d*)',
    ]

    SEMANTIC_PATTERNS = [
        r'best (for|to)',
        r'(good|suitable|work well) (for|with)',
        r'recommend',
        r'suggest',
        r'(what|which) (\w+) (for|to)',
    ]

    COMPARISON_PATTERNS = [
        r'compare (\w+) (and|vs|versus) (\w+)',
        r'difference between (\w+) and (\w+)',
        r"what's the difference",
        r'(\w+) vs (\w+)',
    ]

    WORKFLOW_PATTERNS = [
        r'how (do|can) I',
        r'what\'?s the command',
        r'how to (load|set|change|automate)',
    ]

    def __init__(self):
        logger.info("[HelpRouter] Initialized")

    def classify_query(self, query: str) -> Tuple[QueryType, Dict[str, Any]]:
        """
        Classify query and extract entities

        Returns:
            (QueryType, metadata_dict)
        """
        query_lower = query.lower()

        # Check each pattern type in priority order (most specific first!)
        # 1. Count queries (most specific)
        for pattern in self.COUNT_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                device = self._extract_device(match.groups())
                if device:
                    logger.info(f"[HelpRouter] Classified as FACTUAL_COUNT: device={device}")
                    return QueryType.FACTUAL_COUNT, {'device': device}

        # 2. Semantic queries (best for, recommend) - CHECK BEFORE LIST!
        for pattern in self.SEMANTIC_PATTERNS:
            if re.search(pattern, query_lower):
                logger.info(f"[HelpRouter] Classified as SEMANTIC")
                return QueryType.SEMANTIC, {}

        # 3. Comparison queries
        for pattern in self.COMPARISON_PATTERNS:
            if re.search(pattern, query_lower):
                logger.info(f"[HelpRouter] Classified as COMPARISON")
                return QueryType.COMPARISON, {}

        # 4. List queries (broader pattern - check after semantic/comparison)
        for pattern in self.LIST_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                device = self._extract_device(match.groups())
                if device:
                    # Check if IDs requested
                    include_ids = 'id' in query_lower or 'ids' in query_lower
                    logger.info(f"[HelpRouter] Classified as FACTUAL_LIST: device={device}, ids={include_ids}")
                    return QueryType.FACTUAL_LIST, {'device': device, 'include_ids': include_ids}

        # 5. Parameter queries
        for pattern in self.PARAM_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                device = self._extract_device(match.groups())
                if device:
                    logger.info(f"[HelpRouter] Classified as FACTUAL_PARAMS: device={device}")
                    return QueryType.FACTUAL_PARAMS, {'device': device}

        # 6. Parameter search queries
        for pattern in self.PARAM_SEARCH_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                groups = match.groups()
                device = self._extract_device(groups)
                param_name, operator, value = self._extract_param_constraint(groups, query_lower)

                if device and param_name:
                    logger.info(f"[HelpRouter] Classified as PARAMETER_SEARCH: {device}.{param_name} {operator} {value}")
                    return QueryType.PARAMETER_SEARCH, {
                        'device': device,
                        'param_name': param_name,
                        'operator': operator,
                        'value': value
                    }

        # 7. Workflow queries
        for pattern in self.WORKFLOW_PATTERNS:
            if re.search(pattern, query_lower):
                logger.info(f"[HelpRouter] Classified as WORKFLOW")
                return QueryType.WORKFLOW, {}

        # 8. Default to complex RAG
        logger.info(f"[HelpRouter] Classified as COMPLEX (default)")
        return QueryType.COMPLEX, {}

    def _extract_device(self, groups: tuple) -> Optional[str]:
        """Extract device name from regex groups"""
        for item in groups:
            if isinstance(item, str):
                item_lower = item.lower()
                if item_lower in self.DEVICES:
                    return item_lower
        return None

    def _extract_param_constraint(self, groups: tuple, query: str) -> Tuple[Optional[str], str, float]:
        """Extract parameter name, operator, and value from query"""
        # Common parameter names
        params = {
            'decay': ['decay', 'decay time', 'reverb time'],
            'room size': ['room', 'room size', 'size'],
            'feedback': ['feedback', 'regen'],
            'ratio': ['ratio', 'compression ratio'],
            'threshold': ['threshold', 'thresh'],
            'attack': ['attack'],
            'release': ['release'],
        }

        # Find parameter name in query
        param_name = None
        for canonical, variants in params.items():
            for variant in variants:
                if variant in query:
                    param_name = canonical
                    break
            if param_name:
                break

        # Determine operator
        operator = 'less_than'  # default
        if any(word in query for word in ['greater', 'over', 'above', 'larger', '>']):
            operator = 'greater_than'

        # Extract value (last number in groups)
        value = 0.0
        for item in reversed(groups):
            if isinstance(item, str):
                try:
                    value = float(item)
                    break
                except ValueError:
                    continue

        return param_name, operator, value

    def should_use_firestore(self, query_type: QueryType) -> bool:
        """Determine if query should use Firestore direct"""
        return query_type in [
            QueryType.FACTUAL_COUNT,
            QueryType.FACTUAL_LIST,
            QueryType.FACTUAL_PARAMS,
            QueryType.PARAMETER_SEARCH,
        ]

    def should_use_vector_search(self, query_type: QueryType) -> bool:
        """Determine if query should use vector search (future)"""
        return query_type == QueryType.SEMANTIC

    def should_use_rag(self, query_type: QueryType) -> bool:
        """Determine if query needs full RAG"""
        return query_type in [
            QueryType.COMPARISON,
            QueryType.WORKFLOW,
            QueryType.COMPLEX,
        ]

    def estimate_response_time(self, query_type: QueryType) -> float:
        """Estimate response time in seconds"""
        if self.should_use_firestore(query_type):
            return 0.1
        elif self.should_use_vector_search(query_type):
            return 1.5
        else:
            return 8.0


# Singleton
_router = None

def get_help_router() -> HelpRouter:
    """Get or create HelpRouter singleton"""
    global _router
    if _router is None:
        _router = HelpRouter()
    return _router
