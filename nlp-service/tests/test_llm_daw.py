import os
import sys

# Make the nlp-service/ directory importable
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from llm_daw import interpret_daw_command


def test_relative_change_volume_parsing():
    os.environ["LLM_MODEL_PREFERENCE"] = "gemini-2.5-flash"
    result = interpret_daw_command("increase track 2 volume by 3 dB")
    assert isinstance(result, dict)
    assert result.get("intent") in ("relative_change", "set_parameter")
    # Accept either relative_change or set_parameter with relative op
    op = result.get("operation", {})
    assert op.get("unit", "").lower() == "db"
    assert "targets" in result and isinstance(result["targets"], list)


def test_question_response_soft_vocals():
    result = interpret_daw_command("vocals are too soft")
    assert result.get("intent") == "question_response"
    assert "answer" in result


def test_clarification_for_garbage():
    result = interpret_daw_command("asdfghjk")
    assert result.get("intent") == "clarification_needed"
    assert "question" in result
