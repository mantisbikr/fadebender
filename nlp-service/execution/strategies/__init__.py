"""Execution strategies for different NLP modes."""

__all__ = ["regex_first", "llm_first", "regex_only", "llm_only", "parallel"]

from execution.strategies import regex_first, llm_first, regex_only, llm_only, parallel
