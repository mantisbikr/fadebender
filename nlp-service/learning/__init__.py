"""Learning module for capturing and persisting typo corrections."""

from learning.typo_learner import learn_from_llm_success, detect_typos
from learning.typo_persister import persist_typos, can_persist

__all__ = ['learn_from_llm_success', 'detect_typos', 'persist_typos', 'can_persist']
