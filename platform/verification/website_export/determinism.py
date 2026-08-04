"""Determinism verification for website-safe export."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.website_export import (
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    report_to_stable_dict,
)

from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_determinism(verified: VerifiedExportInput) -> list[CheckResult]:
    left = build_website_safe_export(
        verified.report, policy=verified.policy, generated_at=None
    )
    right = build_website_safe_export(
        verified.report, policy=verified.policy, generated_at=None
    )
    payload = report_to_stable_dict(verified.report)
    restored = from_stable_dict(payload)
    via_restore = build_website_safe_export(
        restored, policy=verified.policy, generated_at=None
    )
    return [
        CheckResult(
            name="determinism:json_bytes",
            ok=left.json_bytes == right.json_bytes == verified.bundle.json_bytes,
            detail="stable json",
            category="determinism",
        ),
        CheckResult(
            name="determinism:html_bytes",
            ok=left.html_bytes == right.html_bytes == verified.bundle.html_bytes,
            detail="stable html",
            category="determinism",
        ),
        CheckResult(
            name="determinism:manifest_bytes",
            ok=left.manifest_bytes == right.manifest_bytes == verified.bundle.manifest_bytes,
            detail="stable manifest",
            category="determinism",
        ),
        CheckResult(
            name="determinism:export_id",
            ok=(
                left.document.export_metadata.export_id  # type: ignore[union-attr]
                == right.document.export_metadata.export_id  # type: ignore[union-attr]
                == verified.bundle.document.export_metadata.export_id  # type: ignore[union-attr]
            ),
            detail="stable export id",
            category="determinism",
        ),
        CheckResult(
            name="determinism:roundtrip_report",
            ok=(
                via_restore.json_bytes == left.json_bytes
                and via_restore.html_bytes == left.html_bytes
                and via_restore.manifest_bytes == left.manifest_bytes
            ),
            detail="serialize/deserialize EIR",
            category="determinism",
        ),
    ]
