"""Validation checks for duplicate Finding projections (Slice 5.11)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from codestrata.application.findings.consolidation import consolidate_findings
from codestrata.domain.findings.models import Finding


def detect_duplicate_finding_issues(
    findings: Sequence[Finding] | Sequence[dict[str, Any]],
) -> tuple[str, ...]:
    """Return diagnostics for duplicate IDs / same-rule same-condition Findings.

    Does not fail the suite by itself; callers decide whether to surface them.
    """

    parsed: list[Finding] = []
    for item in findings:
        if isinstance(item, Finding):
            parsed.append(item)
        elif isinstance(item, dict):
            try:
                parsed.append(Finding.model_validate(item))
            except Exception:  # noqa: BLE001
                continue
    if not parsed:
        return ()

    diagnostics: list[str] = []
    seen_ids: set[str] = set()
    for item in parsed:
        if item.id in seen_ids:
            diagnostics.append(f"duplicate_finding_id:{item.id}")
        seen_ids.add(item.id)

    result = consolidate_findings(parsed)
    if result.diagnostics.equivalent_duplicate_count:
        diagnostics.append(
            "equivalent_same_rule_duplicates="
            f"{result.diagnostics.equivalent_duplicate_count}"
        )
    if result.diagnostics.exact_duplicate_count:
        diagnostics.append(
            f"exact_duplicates={result.diagnostics.exact_duplicate_count}"
        )
    for group in result.duplicate_groups:
        diagnostics.append(
            f"duplicate_group:{group.duplicate_kind.value}:"
            f"{group.canonical_finding_id}:"
            f"{','.join(group.member_finding_ids)}"
        )
    return tuple(sorted(set(diagnostics)))
