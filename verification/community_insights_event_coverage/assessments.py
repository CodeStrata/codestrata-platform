"""Assessment lifecycle metric helpers."""

from __future__ import annotations

from typing import Any


def assessment_rules() -> dict[str, Any]:
    return {
        "first_repeat_derive_not_flag": True,
        "success_fields": [
            "payload.assessment.assessment_status",
            "payload.execution.result",
        ],
        "not_failure_signals": ["open_report", "report_json_generated"],
    }
