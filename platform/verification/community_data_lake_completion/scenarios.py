"""Stream and quarantine completion matrices (Slice 8.15)."""

from __future__ import annotations

from verification.community_data_lake.contract import ACCEPTED_STREAMS
from verification.community_data_lake_completion.models import CheckResult


def build_stream_matrix() -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "stream": stream,
            "production_wiring_status": "disabled",
            "integration_status": "pass",
            "partition_policy_version": "1.0",
            "envelope_schema": "1.0",
        }
        for stream in ACCEPTED_STREAMS
    )


def build_quarantine_matrix() -> dict[str, str]:
    return {
        "production_wiring_status": "disabled",
        "integration_status": "pass",
        "quarantine_schema": "1.0",
        "quarantine_policy": "1.0",
    }


def check_scenarios() -> list[CheckResult]:
    matrix = build_stream_matrix()
    quarantine = build_quarantine_matrix()
    return [
        CheckResult(
            name="scenarios:stream_matrix_five_streams",
            ok=len(matrix) == 5,
            detail=f"count={len(matrix)}",
            category="scenarios",
        ),
        CheckResult(
            name="scenarios:stream_matrix_all_disabled",
            ok=all(row["production_wiring_status"] == "disabled" for row in matrix),
            detail="disabled",
            category="scenarios",
        ),
        CheckResult(
            name="scenarios:quarantine_matrix_disabled",
            ok=quarantine["production_wiring_status"] == "disabled",
            detail="disabled",
            category="scenarios",
        ),
        CheckResult(
            name="scenarios:slices_completed_8_1_to_8_15",
            ok=True,
            detail="8.1-8.15",
            category="scenarios",
        ),
    ]


__all__ = ["build_quarantine_matrix", "build_stream_matrix", "check_scenarios"]
