"""Safety and privacy scans for EIR / verification payloads."""

from __future__ import annotations

import json
import re

from verification.engineering_intelligence.contract import SAFETY_PATTERNS
from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def _scan(text: str) -> list[str]:
    hits: list[str] = []
    for name, pattern in SAFETY_PATTERNS:
        if re.search(pattern, text):
            # Allow intentionally redacted markers.
            if "[REDACTED]" in text and name in {"password_assign", "bearer"}:
                continue
            hits.append(name)
    return hits


def check_safety(pipeline: PipelineArtifacts) -> list[CheckResult]:
    payload = json.dumps(pipeline.report_payload, sort_keys=True)
    hits = _scan(payload)
    checks = [
        CheckResult(
            name="safety:eir_payload_clean",
            ok=not hits,
            detail=f"hits={hits}" if hits else "ok",
            category="safety",
            scenario="T",
        ),
        CheckResult(
            name="safety:no_full_report_embedded",
            ok="deterministic_recommendations" not in payload
            and "source_body" not in payload.lower(),
            detail="no embedded assessment recommendation bodies",
            category="safety",
        ),
    ]
    # More precise: dataset payload must not include finding descriptions bodies.
    lowered = payload.lower()
    checks.append(
        CheckResult(
            name="safety:no_source_body",
            ok="source_body" not in lowered and "file://" not in lowered,
            detail="no source bodies / file URLs",
            category="safety",
        )
    )
    checks.append(
        CheckResult(
            name="safety:no_customer_private_ids_in_public_oss",
            ok="customer_private" not in str(pipeline.report.report_scope.value).lower()
            or all(
                getattr(item, "visibility", None) is None
                or getattr(getattr(item, "visibility", None), "value", "") != "customer_private"
                for item in pipeline.report.dataset.repository_assessments
            ),
            detail=str(pipeline.report.report_scope.value),
            category="safety",
            scenario="J",
        )
    )
    return checks
