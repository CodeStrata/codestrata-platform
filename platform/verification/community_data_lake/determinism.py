"""Determinism checks for Community Data Lake verification (Slice 8.14)."""

from __future__ import annotations

from verification.community_data_lake.inputs import (
    project_quarantine_object,
    project_stream_storage_object,
)
from verification.community_data_lake.models import CheckResult


def check_determinism() -> list[CheckResult]:
    checks: list[CheckResult] = []

    first = project_stream_storage_object("telemetry")
    second = project_stream_storage_object("telemetry")
    checks.extend(
        [
            CheckResult(
                name="determinism:telemetry:bytes",
                ok=first.canonical_json_bytes == second.canonical_json_bytes,
                detail="bytes stable",
                category="determinism",
            ),
            CheckResult(
                name="determinism:telemetry:digest",
                ok=first.content_sha256 == second.content_sha256,
                detail="digest stable",
                category="determinism",
            ),
            CheckResult(
                name="determinism:telemetry:key",
                ok=first.object_key == second.object_key,
                detail="key stable",
                category="determinism",
            ),
            CheckResult(
                name="determinism:telemetry:metadata",
                ok=first.to_s3_metadata() == second.to_s3_metadata(),
                detail="metadata stable",
                category="determinism",
            ),
        ]
    )

    q_first = project_quarantine_object()
    q_second = project_quarantine_object()
    checks.extend(
        [
            CheckResult(
                name="determinism:quarantine:bytes",
                ok=q_first.canonical_json_bytes == q_second.canonical_json_bytes,
                detail="bytes stable",
                category="determinism",
            ),
            CheckResult(
                name="determinism:quarantine:digest",
                ok=q_first.content_sha256 == q_second.content_sha256,
                detail="digest stable",
                category="determinism",
            ),
            CheckResult(
                name="determinism:quarantine:key",
                ok=q_first.object_key == q_second.object_key,
                detail="key stable",
                category="determinism",
            ),
        ]
    )

    return checks


__all__ = ["check_determinism"]
