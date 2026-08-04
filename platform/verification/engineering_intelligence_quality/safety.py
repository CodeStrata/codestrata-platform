"""Website-safe export review (reuses SV.8 matcher style)."""

from __future__ import annotations

import re
from typing import Any

from verification.engineering_intelligence.contract import SAFETY_PATTERNS
from verification.engineering_intelligence_quality.contract import (
    EXPORT_MANIFEST,
    REPORT_HTML,
    REPORT_JSON,
    UNSUPPORTED_COMMERCIAL_CLAIMS,
)
from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)


def review_safety(
    *,
    output_dir,
    json_text: str,
    html_text: str,
    manifest_payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []

    for name in (REPORT_JSON, REPORT_HTML, EXPORT_MANIFEST):
        if not (output_dir / name).is_file():
            defects.append(
                DefectCandidate(
                    classification="website_safety",
                    statement=f"missing export artifact {name}",
                    section="website_export",
                    release_impact="blocking",
                    recommended_handling="verification_harness_fix",
                )
            )

    hits: list[str] = []
    for label, pattern in SAFETY_PATTERNS:
        if re.search(pattern, json_text) or re.search(pattern, html_text):
            hits.append(label)
    if hits:
        defects.append(
            DefectCandidate(
                classification="website_safety",
                statement=f"safety pattern hits: {','.join(hits[:8])}",
                section="website_export",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )

    lowered = f"{json_text}\n{html_text}".lower()
    for marker in ('"evidence_body"', '"source_snippet"', '"graph_payload"', "file://"):
        if marker in lowered:
            defects.append(
                DefectCandidate(
                    classification="website_safety",
                    statement=f"forbidden projection marker: {marker}",
                    section="website_export",
                    release_impact="blocking",
                    recommended_handling="SV.13_product_fix",
                )
            )

    # CSP / no script
    if "content-security-policy" not in html_text.lower():
        defects.append(
            DefectCandidate(
                classification="website_safety",
                statement="HTML CSP missing",
                section="website_export",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )
    if re.search(r"<script[\s>]", html_text, re.I):
        defects.append(
            DefectCandidate(
                classification="website_safety",
                statement="HTML contains script tags",
                section="website_export",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )

    for frag in ("maturity score", "health score", "industry benchmark"):
        if frag in lowered:
            idx = lowered.find(frag)
            window = lowered[max(0, idx - 30) : idx + len(frag) + 30]
            if not any(n in window for n in ("not ", "no ", "does not", "without ")):
                defects.append(
                    DefectCandidate(
                        classification="website_safety",
                        statement=f"unsupported fragment in export: {frag}",
                        section="website_export",
                        release_impact="blocking",
                        recommended_handling="SV.13_product_fix",
                    )
                )

    # Manifest digests presence
    arts = manifest_payload.get("artifacts") or []
    if not arts:
        observations.append(
            EditorialObservation(
                observation_id="manifest-empty",
                section="website_export",
                classification="unclear",
                statement="Export manifest artifacts list empty or unexpected shape",
                recommended_handling="documentation_only",
            )
        )

    observations.append(
        EditorialObservation(
            observation_id="website-safe-ok",
            section="website_export",
            classification="useful",
            statement=(
                f"Website-safe JSON={len(json_text)}B HTML={len(html_text)}B; "
                "CSP and allowlisted projection expected"
            ),
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "json_bytes": len(json_text.encode("utf-8")),
        "html_bytes": len(html_text.encode("utf-8")),
        "summary": "Website-safe export reviewed for CSP, secrets, and allowlisted projection",
    }
    return review, observations, defects
