"""TEST-ONLY AI readiness signal module.

Filename includes ``openai`` so AI-readiness discovery classifies this path.
Imports the OpenAI SDK name for static detection. Does not create clients,
does not read API keys, and does not call any network endpoint.
"""

from __future__ import annotations

# Intentional static signal for ai_readiness.ai-030 (LLM SDK).
import openai  # noqa: F401


def describe_fixture() -> str:
    return "codestrata ai-readiness fixture (no network calls)"
