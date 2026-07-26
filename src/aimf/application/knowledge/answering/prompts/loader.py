"""Deterministic loader and renderer for external grounded-answer prompts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any, Literal

from aimf.application.knowledge.answering.safety import scrub_text
from aimf.domain.knowledge.answering import AnswerStyle
from aimf.domain.knowledge.retrieval import RetrievalHit

DEFAULT_PROMPT_NAME = "grounded-repository-answer"
DEFAULT_PROMPT_VERSION = "1.0.0"
PROMPT_VERSION = f"{DEFAULT_PROMPT_NAME}/{DEFAULT_PROMPT_VERSION}"

_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
_TEMPLATE_FILES = {
    "system": "system.md",
    "user": "user.md",
    "repair": "repair.md",
}
TemplateKind = Literal["system", "user", "repair"]

_PACKAGE = "aimf.application.knowledge.answering.prompts"


class PromptResourceError(ValueError):
    """Raised when a prompt resource cannot be loaded or rendered."""


@dataclass(frozen=True)
class PromptMetadata:
    name: str
    version: str
    response_schema_version: str
    required_variables: Mapping[str, tuple[str, ...]]

    @property
    def prompt_version(self) -> str:
        return f"{self.name}/{self.version}"


@dataclass(frozen=True)
class PromptBundle:
    """Loaded prompt templates and metadata for one name/version."""

    metadata: PromptMetadata
    system: str
    user: str
    repair: str
    response_schema: dict[str, Any]

    @property
    def prompt_version(self) -> str:
        return self.metadata.prompt_version


def prompt_resource_root() -> Traversable:
    """Return the importlib resources root for prompt packages."""

    return files(_PACKAGE)


def prompt_version_path(name: str, version: str) -> Traversable:
    """Return the resource path for a prompt version directory."""

    return prompt_resource_root().joinpath(name).joinpath(version)


def _read_text(resource: Traversable, *, label: str) -> str:
    try:
        return str(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, AttributeError) as exc:
        raise PromptResourceError(f"failed to read prompt resource {label}: {exc}") from exc


def _parse_metadata(raw: str) -> PromptMetadata:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PromptResourceError(f"prompt metadata is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PromptResourceError("prompt metadata must be a JSON object")
    name = str(payload.get("name") or "").strip()
    version = str(payload.get("version") or "").strip()
    schema_version = str(payload.get("response_schema_version") or "").strip()
    required_raw = payload.get("required_variables")
    if not name or not version or not schema_version:
        raise PromptResourceError(
            "prompt metadata requires name, version, and response_schema_version"
        )
    if not isinstance(required_raw, dict):
        raise PromptResourceError("prompt metadata.required_variables must be an object")
    required: dict[str, tuple[str, ...]] = {}
    for key, value in required_raw.items():
        if not isinstance(value, list):
            raise PromptResourceError(
                f"required_variables.{key} must be a list of variable names"
            )
        required[str(key)] = tuple(str(item) for item in value)
    return PromptMetadata(
        name=name,
        version=version,
        response_schema_version=schema_version,
        required_variables=required,
    )


@lru_cache(maxsize=16)
def load_prompt_bundle(
    name: str = DEFAULT_PROMPT_NAME,
    version: str = DEFAULT_PROMPT_VERSION,
) -> PromptBundle:
    """Load and validate an external prompt version (cached, deterministic)."""

    compact_name = name.strip()
    compact_version = version.strip()
    if not compact_name:
        raise PromptResourceError("prompt name must be nonempty")
    if not compact_version:
        raise PromptResourceError("prompt version must be nonempty")

    root = prompt_resource_root()
    name_dir = root.joinpath(compact_name)
    if not name_dir.is_dir():
        raise PromptResourceError(f"unknown prompt {compact_name!r}")

    version_dir = name_dir.joinpath(compact_version)
    if not version_dir.is_dir():
        raise PromptResourceError(
            f"unknown prompt version {compact_name!r}/{compact_version!r}"
        )

    metadata = _parse_metadata(
        _read_text(version_dir.joinpath("metadata.json"), label="metadata.json")
    )
    if metadata.name != compact_name or metadata.version != compact_version:
        raise PromptResourceError(
            "prompt metadata name/version mismatch: "
            f"expected {compact_name}/{compact_version}, "
            f"got {metadata.name}/{metadata.version}"
        )

    templates: dict[str, str] = {}
    for kind, filename in _TEMPLATE_FILES.items():
        text = _read_text(version_dir.joinpath(filename), label=filename).rstrip() + "\n"
        _validate_template_placeholders(
            text,
            required=metadata.required_variables.get(kind, ()),
            label=f"{compact_name}/{compact_version}/{filename}",
        )
        templates[kind] = text

    schema_raw = _read_text(
        version_dir.joinpath("response_schema.json"),
        label="response_schema.json",
    )
    try:
        schema = json.loads(schema_raw)
    except json.JSONDecodeError as exc:
        raise PromptResourceError(f"response_schema.json is not valid JSON: {exc}") from exc
    if not isinstance(schema, dict):
        raise PromptResourceError("response_schema.json must be a JSON object")

    return PromptBundle(
        metadata=metadata,
        system=templates["system"],
        user=templates["user"],
        repair=templates["repair"],
        response_schema=schema,
    )


def clear_prompt_cache() -> None:
    """Clear the prompt bundle cache (tests)."""

    load_prompt_bundle.cache_clear()


def _placeholders(template: str) -> set[str]:
    return set(_PLACEHOLDER.findall(template))


def _validate_template_placeholders(
    template: str,
    *,
    required: Sequence[str],
    label: str,
) -> None:
    found = _placeholders(template)
    required_set = set(required)
    missing = sorted(required_set - found)
    unknown = sorted(found - required_set)
    if missing:
        raise PromptResourceError(
            f"prompt template {label} missing required placeholders: {missing}"
        )
    if unknown:
        raise PromptResourceError(
            f"prompt template {label} has unknown placeholders: {unknown}"
        )


def render_template(
    template: str,
    variables: Mapping[str, str],
    *,
    required: Sequence[str],
    label: str,
) -> str:
    """Render a template with strict required/unknown variable validation."""

    required_set = set(required)
    provided = set(variables)
    missing = sorted(required_set - provided)
    unknown = sorted(provided - required_set)
    if missing:
        raise PromptResourceError(
            f"missing required variables for {label}: {missing}"
        )
    if unknown:
        raise PromptResourceError(
            f"unknown variables for {label}: {unknown}"
        )
    try:
        return template.format(**{key: variables[key] for key in sorted(required_set)})
    except KeyError as exc:  # pragma: no cover - guarded above
        raise PromptResourceError(f"missing variable while rendering {label}: {exc}") from exc


def render_evidence_blocks(hits: Sequence[RetrievalHit], *, max_chars: int = 12_000) -> str:
    blocks: list[str] = []
    used = 0
    for hit in hits:
        content = scrub_text(hit.content or "")
        if not content:
            continue
        block = (
            f"[{hit.citation_label}] record_id={hit.record_id}\n"
            f"source_type={hit.source_type or ''} file={hit.file_path or ''}\n"
            f"{content}"
        )
        if used + len(block) > max_chars and blocks:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n---\n\n".join(blocks) if blocks else "(no evidence)"


def get_system_prompt(
    *,
    name: str = DEFAULT_PROMPT_NAME,
    version: str = DEFAULT_PROMPT_VERSION,
) -> str:
    return load_prompt_bundle(name, version).system.rstrip() + "\n"


def get_response_schema(
    *,
    name: str = DEFAULT_PROMPT_NAME,
    version: str = DEFAULT_PROMPT_VERSION,
) -> dict[str, Any]:
    return dict(load_prompt_bundle(name, version).response_schema)


def build_user_prompt(
    *,
    question: str,
    style: AnswerStyle | str,
    hits: Sequence[RetrievalHit],
    citation_labels: Sequence[str],
    name: str = DEFAULT_PROMPT_NAME,
    version: str = DEFAULT_PROMPT_VERSION,
) -> str:
    bundle = load_prompt_bundle(name, version)
    style_value = style.value if isinstance(style, AnswerStyle) else str(style)
    evidence_ids = tuple(hit.record_id for hit in hits)
    rendered = render_template(
        bundle.user,
        {
            "question": scrub_text(question),
            "style": style_value,
            "citation_labels": ", ".join(citation_labels) or "(none)",
            "evidence_ids": ", ".join(evidence_ids) or "(none)",
            "evidence_blocks": render_evidence_blocks(hits),
            "response_schema": json.dumps(bundle.response_schema, sort_keys=True),
        },
        required=bundle.metadata.required_variables.get("user", ()),
        label=f"{bundle.prompt_version}/user.md",
    )
    return rendered.rstrip() + "\n"


def build_repair_prompt(
    *,
    error: str,
    citation_labels: Sequence[str],
    name: str = DEFAULT_PROMPT_NAME,
    version: str = DEFAULT_PROMPT_VERSION,
) -> str:
    bundle = load_prompt_bundle(name, version)
    rendered = render_template(
        bundle.repair,
        {
            "error": scrub_text(error),
            "citation_labels": ", ".join(citation_labels) or "(none)",
            "response_schema": json.dumps(bundle.response_schema, sort_keys=True),
        },
        required=bundle.metadata.required_variables.get("repair", ()),
        label=f"{bundle.prompt_version}/repair.md",
    )
    return rendered.rstrip() + "\n"


def __getattr__(name: str) -> Any:
    """Lazy aliases so prompt text is never stored as Python literals."""

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
