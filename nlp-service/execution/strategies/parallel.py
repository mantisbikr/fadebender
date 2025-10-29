"""Parallel strategy: Run both pipelines, return faster, log comparison.

TESTING mode - for A/B testing and comparison analysis.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from models.intent_types import Intent
from execution.regex_executor import try_regex_parse
from execution.llm_executor import call_llm
from execution.response_builder import build_clarification_response


def execute(query: str, model_preference: str | None, strict: bool | None) -> Intent:
    """Run both pipelines, return faster one, log comparison.

    Args:
        query: User query text
        model_preference: LLM model preference
        strict: Not used (parallel mode doesn't raise exceptions)

    Returns:
        Intent dictionary with comparison metadata
    """
    start = time.perf_counter()
    results = {}
    lock = threading.Lock()

    def run_regex():
        result, _ = try_regex_parse(query, "", model_preference)
        with lock:
            results['regex'] = result if result else None

    def run_llm():
        try:
            result = call_llm(query, model_preference)
            with lock:
                results['llm'] = result
        except Exception as e:
            with lock:
                results['llm'] = None
                results['llm_error'] = str(e)

    # Run both in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        regex_future = executor.submit(run_regex)
        llm_future = executor.submit(run_llm)

        # Wait for both to complete
        regex_future.result()
        llm_future.result()

    # Determine which one to return
    regex_result = results.get('regex')
    llm_result = results.get('llm')

    total_latency = (time.perf_counter() - start) * 1000

    # If regex succeeded, use it (usually faster)
    if regex_result:
        result = regex_result
        result['meta']['pipeline'] = 'parallel_regex_won'
        result['meta']['total_latency_ms'] = total_latency
        result['meta']['comparison'] = {
            'regex_succeeded': True,
            'llm_succeeded': llm_result is not None,
            'llm_error': results.get('llm_error')
        }
        return result

    # Regex failed, use LLM if available
    if llm_result:
        result = llm_result
        result['meta']['pipeline'] = 'parallel_llm_won'
        result['meta']['total_latency_ms'] = total_latency
        result['meta']['comparison'] = {
            'regex_succeeded': False,
            'llm_succeeded': True
        }
        return result

    # Both failed
    return build_clarification_response(
        query,
        results.get('llm_error', 'Both parsers failed'),
        model_preference,
        start
    )
