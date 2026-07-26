"""External versioned grounded-answer prompts (Phase 5.8.1).

Production prompt text lives under versioned resource directories. This package
exposes only loading, rendering, validation, and resource-path helpers.
"""

from __future__ import annotations

from typing import Any

from aimf.application.knowledge.answering.prompts.loader import (
    DEFAULT_PROMPT_NAME,
    DEFAULT_PROMPT_VERSION,
    PROMPT_VERSION,
    PromptBundle,
    PromptMetadata,
    PromptResourceError,
    build_repair_prompt,
    build_user_prompt,
    clear_prompt_cache,
    get_response_schema,
    get_system_prompt,
    load_prompt_bundle,
    prompt_resource_root,
    prompt_version_path,
    render_evidence_blocks,
    render_template,
)


def __getattr__(name: str) -> Any:
    if name == "SYSTEM_PROMPT":
        return get_system_prompt()
    if name == "RESPONSE_SCHEMA":
        return get_response_schema()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DEFAULT_PROMPT_NAME",
    "DEFAULT_PROMPT_VERSION",
    "PROMPT_VERSION",
    "PromptBundle",
    "PromptMetadata",
    "PromptResourceError",
    "RESPONSE_SCHEMA",
    "SYSTEM_PROMPT",
    "build_repair_prompt",
    "build_user_prompt",
    "clear_prompt_cache",
    "get_response_schema",
    "get_system_prompt",
    "load_prompt_bundle",
    "prompt_resource_root",
    "prompt_version_path",
    "render_evidence_blocks",
    "render_template",
]
