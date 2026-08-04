"""Canonical fingerprints over safe deterministic representations."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from codestrata.reporting.contract.canonical import strip_volatile_fields


# Absolute harness / machine paths. Do not use bare "/users/" substrings —
# repository-relative paths such as app/Users/Models or factories/users are
# legitimate. Align with website-export / curated-validation privacy scans:
# require a path boundary, and ignore OSS CI /home/runner references.
_OPERATOR_HOME_RE = re.compile(r"(?<![\w.-])(/Users/|/home/)([\w.-]+)")
_HARNESS_TMP_RE = re.compile(
    r"(?<![\w.-])(/var/folders/|/private/var/|/private/tmp/)"
)
_OBJECT_ADDR_RE = re.compile(r"object at 0x[0-9a-fA-F]+")
_PID_ASSIGN_RE = re.compile(r"(?<![A-Za-z0-9_])pid=\d+")


def stable_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def fingerprint_assessment_report(document: dict[str, Any]) -> str:
    canonical = strip_volatile_fields(document)
    return sha256_hex(stable_json_bytes(canonical))


def fingerprint_mapping(payload: dict[str, Any], *, exclude: tuple[str, ...] = ()) -> str:
    copy = json.loads(json.dumps(payload))
    for key in exclude:
        copy.pop(key, None)
    return sha256_hex(stable_json_bytes(copy))


def contains_forbidden_environment(text: str) -> list[str]:
    """Return forbidden environment-derived tokens found in text.

    Does not flag:
    - repository-relative segments containing ``users`` / ``Users``
    - documented OSS CI paths such as ``/home/runner``
    - ``/tmp/`` references that appear inside assessed repository evidence
      (those are source content, not CodeStrata harness identity)
    """

    hits: list[str] = []
    for match in _OPERATOR_HOME_RE.finditer(text):
        user = match.group(2).lower()
        if user == "runner":
            continue
        hits.append("operator_home_path")
        break
    if _HARNESS_TMP_RE.search(text):
        hits.append("harness_tmp_path")
    if _OBJECT_ADDR_RE.search(text):
        hits.append("object at 0x")
    if _PID_ASSIGN_RE.search(text):
        hits.append("pid")
    return sorted(set(hits))
