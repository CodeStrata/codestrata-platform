"""Acceptance RAG helpers exposed to Community via entry points."""

from __future__ import annotations

from types import SimpleNamespace

from codestrata_platform.rag.acceptance import qa as _qa

helpers = SimpleNamespace(
    ask_predefined_questions=_qa.ask_predefined_questions,
    build_answer_stack=_qa.build_answer_stack,
    load_corpus_from_run=_qa.load_corpus_from_run,
    mcp_health_check=_qa.mcp_health_check,
)

ask_predefined_questions = _qa.ask_predefined_questions
build_answer_stack = _qa.build_answer_stack
load_corpus_from_run = _qa.load_corpus_from_run
mcp_health_check = _qa.mcp_health_check

__all__ = [
    "ask_predefined_questions",
    "build_answer_stack",
    "helpers",
    "load_corpus_from_run",
    "mcp_health_check",
]
