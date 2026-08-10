"""Shared helpers for Slice 17.20 verification."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from verification.community_ai_providers.models import CheckResult, Defect

# Never print secret values. Patterns forbid credential shapes in reports.
FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"cscc_v1_"),
    # OpenAI / OpenRouter key shapes (avoid matching substrings like flask-2026…)
    re.compile(r"(?<![A-Za-z0-9])sk-(?:proj-|or-v1-)?[A-Za-z0-9]{16,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{8,}"),
    re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}"),
    re.compile(r"(?<![A-Za-z0-9])ASIA[0-9A-Z]{16}"),
    re.compile(r"aws_secret_access_key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"OPENAI_API_KEY\s*[:=]\s*\S+"),
    re.compile(r"OPENROUTER_API_KEY\s*[:=]\s*\S+"),
    re.compile(r"arn:aws:"),
    re.compile(r"execute-api\."),
    re.compile(r"SecretString"),
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
)

PROVIDER_CALL_MARKERS = (
    re.compile(r"\binvoke_model\b", re.IGNORECASE),
    re.compile(r"\bchat\.completions\.create\b"),
    re.compile(r"\bOpenAI\(", re.IGNORECASE),
    re.compile(r"openrouter\.ai", re.IGNORECASE),
    re.compile(r"bedrock-runtime", re.IGNORECASE),
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    if not isinstance(payload, dict):
        raise TypeError(f"expected object JSON: {path}")
    return payload


def load_json_any(path: Path) -> Any:
    return json.loads(read_text(path))


def contains(path: Path, needle: str) -> bool:
    return needle in read_text(path)


def check(
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
) -> CheckResult:
    return CheckResult(check_id=check_id, ok=bool(ok), detail=detail, category=category)


def hard_defect(
    classification: str,
    check_id: str,
    expected: str,
    detail: str,
) -> Defect:
    return Defect(
        classification=classification,
        check_id=check_id,
        expected=expected,
        detail=detail,
    )


def report_text_is_safe(text: str) -> bool:
    return not any(p.search(text) for p in FORBIDDEN_REPORT_PATTERNS)


def finding_ids_from_findings_json(path: Path) -> set[str]:
    payload = load_json_any(path)
    ids: set[str] = set()
    if isinstance(payload, dict):
        findings = payload.get("findings") or payload.get("items") or []
        if isinstance(findings, list):
            for item in findings:
                if isinstance(item, dict) and item.get("id"):
                    ids.add(str(item["id"]))
        elif isinstance(payload.get("by_id"), dict):
            ids.update(str(k) for k in payload["by_id"])
    elif isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item["id"]))
    return ids


def github_artifact_folder(github_repository: str) -> str:
    owner, _, repo = github_repository.partition("/")
    return f"github-{owner.strip().lower()}-{repo.strip().lower()}"


def env_present(name: str) -> bool:
    import os

    value = os.environ.get(name)
    return bool(value and str(value).strip())


def artifact_dir(item: dict[str, Any], key: str, *, monorepo: Path | None = None) -> Path | None:
    """Resolve an assessment directory from a selection row."""

    private = item.get(f"_{key}_path")
    if isinstance(private, Path):
        return private
    raw = item.get(key)
    if not raw:
        return None
    path = Path(str(raw))
    if path.is_absolute():
        return path
    if monorepo is not None:
        candidate = monorepo / path
        if candidate.exists():
            return candidate
    if str(raw).startswith("tmp/sv17-20-work/"):
        return Path("/" + str(raw))
    return path
