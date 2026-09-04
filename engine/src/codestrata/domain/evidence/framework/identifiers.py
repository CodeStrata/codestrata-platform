"""Deterministic identifiers for evidence framework artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible data deterministically."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def content_digest(value: Any) -> str:
    """Return a SHA-256 digest for JSON-compatible data."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: object) -> str:
    """Return a readable, deterministic identifier from logical identity parts."""

    digest = content_digest([str(part) for part in parts])[:20]
    return f"{prefix}:{digest}"


def evidence_identity(
    *,
    repository_id: str,
    revision: str,
    collector_id: str,
    collector_version: str,
    kind: str,
    payload: Mapping[str, Any],
    locations: Sequence[Mapping[str, Any]],
) -> tuple[str, str]:
    """Return stable evidence ID and material payload digest."""

    payload_sha256 = content_digest(payload)
    evidence_id = stable_id(
        "ev",
        repository_id,
        revision,
        collector_id,
        collector_version,
        kind,
        payload_sha256,
        canonical_json(list(locations)),
    )
    return evidence_id, payload_sha256
