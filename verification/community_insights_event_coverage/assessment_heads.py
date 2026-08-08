"""Assessment head usage helpers."""

from __future__ import annotations

from typing import Any


def head_rules() -> dict[str, Any]:
    return {
        "field": "payload.assessment.executed_heads",
        "findings_forbidden": True,
        "evidence_forbidden": True,
        "canonical_heads": [
            "technology_inventory",
            "architecture",
            "technical_debt",
            "dependency",
            "security",
            "testing",
            "cloud_readiness",
            "ai_readiness",
            "performance",
            "modernization",
        ],
    }
