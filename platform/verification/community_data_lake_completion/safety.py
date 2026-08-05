"""Privacy and documentation safety checks for completion verification (Slice 8.15)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.community_data_lake_completion.contract import FORBIDDEN_REPORT_FRAGMENTS
from verification.community_data_lake_completion.models import CheckResult

REPO = Path(__file__).resolve().parents[3]
DOCS_GLOB = REPO / "platform" / "docs" / "community-cloud-api"


def check_privacy(*, completion_report_path: Path | None = None) -> list[CheckResult]:
    checks: list[CheckResult] = []
    if completion_report_path is not None and completion_report_path.is_file():
        text = completion_report_path.read_text(encoding="utf-8")
        for index, frag in enumerate(FORBIDDEN_REPORT_FRAGMENTS):
            checks.append(
                CheckResult(
                    name=f"privacy:completion_report:no_fragment_{index}",
                    ok=frag not in text,
                    detail="absent",
                    category="privacy",
                )
            )
        payload = json.loads(text)
        checks.append(
            CheckResult(
                name="privacy:completion_report:no_object_key_field",
                ok="object_key" not in text.lower(),
                detail="absent",
                category="privacy",
            )
        )
        checks.append(
            CheckResult(
                name="privacy:completion_report:schema_name_present",
                ok=payload.get("schema_name")
                == "community-data-lake-completion-verification",
                detail="schema",
                category="privacy",
            )
        )
    checks.extend(_check_data_lake_docs())
    return checks


def check_integration_report_privacy(integration_report_path: Path) -> list[CheckResult]:
    if not integration_report_path.is_file():
        return [
            CheckResult(
                name="privacy:integration_report:present",
                ok=False,
                detail="missing",
                category="privacy",
            )
        ]
    text = integration_report_path.read_text(encoding="utf-8")
    checks: list[CheckResult] = []
    for index, frag in enumerate(FORBIDDEN_REPORT_FRAGMENTS):
        checks.append(
            CheckResult(
                name=f"privacy:integration_report:no_fragment_{index}",
                ok=frag not in text,
                detail="absent",
                category="privacy",
            )
        )
    return checks


def _check_data_lake_docs() -> list[CheckResult]:
    checks: list[CheckResult] = []
    doc_paths = sorted(DOCS_GLOB.glob("data-lake*.md"))
    if not doc_paths:
        return [
            CheckResult(
                name="privacy:docs:data_lake_docs_present",
                ok=False,
                detail="missing",
                category="privacy",
            )
        ]

    operational_pattern = re.compile(
        r"production ingestion is operational|exactly-once",
        re.IGNORECASE,
    )
    mitigation_pattern = re.compile(
        r"not operational|unwired|fail-closed|does not claim|not started|disabled|no exactly-once|not claim|no claim",
        re.IGNORECASE,
    )
    claim_failures = 0
    for path in doc_paths:
        text = path.read_text(encoding="utf-8")
        for match in operational_pattern.finditer(text):
            start = max(0, match.start() - 240)
            end = min(len(text), match.end() + 240)
            window = text[start:end]
            matched = match.group(0)
            normalized = re.sub(r"\s+", " ", window.lower())
            if matched.lower().startswith("exactly-once"):
                if "no exactly-once" in normalized or "not claim" in normalized:
                    continue
            ok = bool(mitigation_pattern.search(window))
            if not ok:
                claim_failures += 1
            checks.append(
                CheckResult(
                    name=f"privacy:docs:{path.name}:operational_claim_context",
                    ok=ok,
                    detail=match.group(0)[:40],
                    category="privacy",
                )
            )
    checks.append(
        CheckResult(
            name="privacy:docs:data_lake_docs_scanned",
            ok=claim_failures == 0,
            detail=f"docs={len(doc_paths)};claim_failures={claim_failures}",
            category="privacy",
        )
    )
    return checks


__all__ = ["check_integration_report_privacy", "check_privacy"]
