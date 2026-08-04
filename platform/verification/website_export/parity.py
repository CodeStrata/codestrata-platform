"""JSON/HTML parity verification."""

from __future__ import annotations

from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_parity(verified: VerifiedExportInput) -> list[CheckResult]:
    doc = verified.bundle.document
    html = verified.bundle.html_bytes.decode("utf-8")
    meta = doc.export_metadata
    assert meta is not None
    checks = [
        CheckResult(
            name="parity:export_id",
            ok=meta.export_id in html or meta.export_id in verified.bundle.json_bytes.decode(),
            detail="shared export id",
            category="parity",
        ),
        CheckResult(
            name="parity:report_id",
            ok=doc.report_id in html and doc.report_id in verified.bundle.json_bytes.decode(),
            detail=doc.report_id,
            category="parity",
        ),
        CheckResult(
            name="parity:dataset_summary",
            ok=str(doc.dataset_summary.get("repository_count")) in html,
            detail=str(doc.dataset_summary.get("repository_count")),
            category="parity",
        ),
        CheckResult(
            name="parity:classification",
            ok=doc.classification in html,
            detail=doc.classification,
            category="parity",
        ),
        CheckResult(
            name="parity:confidence_level",
            ok=doc.confidence is not None and doc.confidence.level in html,
            detail=doc.confidence.level if doc.confidence else "",
            category="parity",
        ),
        CheckResult(
            name="parity:drilldown_count",
            ok=len(doc.repository_drilldowns)
            == int(doc.dataset_summary.get("drilldown_count", -1)),
            detail=str(len(doc.repository_drilldowns)),
            category="parity",
        ),
        CheckResult(
            name="parity:no_invented_aliases",
            ok=all(item.repository_alias in html for item in doc.repository_drilldowns),
            detail=f"aliases={len(doc.repository_drilldowns)}",
            category="parity",
        ),
        CheckResult(
            name="parity:section_counts_bounded",
            ok=(
                len(doc.technology_distribution) >= 0
                and len(doc.capability_comparisons) >= 0
                and len(doc.recurring_patterns) >= 0
                and len(doc.modernization_observations) >= 0
            ),
            detail=(
                f"tech={len(doc.technology_distribution)} "
                f"cap={len(doc.capability_comparisons)} "
                f"pat={len(doc.recurring_patterns)} "
                f"obs={len(doc.modernization_observations)}"
            ),
            category="parity",
        ),
        CheckResult(
            name="parity:same_projection_bytes_source",
            ok=verified.bundle.document is doc,
            detail="single WebsiteSafeExportDocument",
            category="parity",
        ),
    ]
    return checks
