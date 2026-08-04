"""HTML export, CSP, section-order, and print verification."""

from __future__ import annotations

import re

from codestrata_platform.intelligence_reporting.application.website_export import (
    CONTENT_SECURITY_POLICY,
    HTML_FILENAME,
)
from codestrata_platform.intelligence_reporting.application.website_export.validation import (
    validate_html_artifact,
)
from codestrata_platform.intelligence_reporting.presentation.static_html.sections import (
    SECTION_ORDER,
)

from verification.website_export.contract import (
    EXPECTED_HTML_TOC_LABELS,
    UNSUPPORTED_SCORE_FRAGMENTS,
)
from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_html_export(verified: VerifiedExportInput) -> list[CheckResult]:
    html = verified.bundle.html_bytes.decode("utf-8")
    lowered = html.lower()
    ids = re.findall(r'\bid="([^"]+)"', html)
    hrefs = re.findall(r'href="#([^"]+)"', html)
    validation_ok = True
    try:
        validate_html_artifact(html)
    except Exception:  # noqa: BLE001
        validation_ok = False

    toc_positions = [lowered.find(label.lower()) for label in EXPECTED_HTML_TOC_LABELS]
    section_positions = []
    for label in EXPECTED_HTML_TOC_LABELS:
        # Prefer h2 headings for body order.
        match = re.search(
            rf"<h2[^>]*>\s*{re.escape(label)}\s*</h2>",
            html,
            flags=re.I,
        )
        section_positions.append(match.start() if match else -1)

    checks = [
        CheckResult(
            name="html:filename_contract",
            ok=HTML_FILENAME == "engineering-intelligence-report.html",
            detail=HTML_FILENAME,
            category="html",
        ),
        CheckResult(
            name="html:doctype_and_shell",
            ok=(
                "<!doctype html>" in lowered
                and lowered.count("<html") == 1
                and "<head" in lowered
                and "<body" in lowered
            ),
            detail="html5 shell",
            category="html",
        ),
        CheckResult(
            name="html:validation",
            ok=validation_ok,
            detail="validate_html_artifact",
            category="html",
        ),
        CheckResult(
            name="html:self_contained",
            ok=(
                "<style>" in lowered
                and 'rel="stylesheet"' not in lowered
                and "<script" not in lowered
                and "<form" not in lowered
                and "<iframe" not in lowered
                and "<object" not in lowered
                and "<embed" not in lowered
            ),
            detail="no external/js/forms",
            category="html",
            scenario="A",
        ),
        CheckResult(
            name="html:csp",
            ok=CONTENT_SECURITY_POLICY in html
            and "script-src 'none'" in CONTENT_SECURITY_POLICY
            and "default-src 'none'" in CONTENT_SECURITY_POLICY
            and "object-src 'none'" in CONTENT_SECURITY_POLICY
            and "form-action 'none'" in CONTENT_SECURITY_POLICY
            and "base-uri 'none'" in CONTENT_SECURITY_POLICY,
            detail="approved CSP",
            category="html",
        ),
        CheckResult(
            name="html:no_inline_handlers",
            ok=not re.search(r"\son\w+\s*=", html, flags=re.I),
            detail="no on*= handlers",
            category="html",
        ),
        CheckResult(
            name="html:section_order_contract",
            ok=SECTION_ORDER[:1] == ("cover",) and "scope" in SECTION_ORDER,
            detail=",".join(SECTION_ORDER),
            category="html",
        ),
        CheckResult(
            name="html:toc_labels_present",
            ok=all(pos >= 0 for pos in toc_positions),
            detail=f"missing={sum(1 for p in toc_positions if p < 0)}",
            category="html",
        ),
        CheckResult(
            name="html:body_section_order",
            ok=(
                all(p >= 0 for p in section_positions)
                and section_positions == sorted(section_positions)
            ),
            detail="h2 order",
            category="html",
        ),
        CheckResult(
            name="html:anchors_unique_resolve",
            ok=len(ids) == len(set(ids)) and set(hrefs).issubset(set(ids)),
            detail=f"ids={len(ids)} hrefs={len(hrefs)}",
            category="html",
        ),
        CheckResult(
            name="html:export_id_or_classification",
            ok=(
                verified.bundle.document.classification in html
                and (
                    verified.bundle.document.export_metadata.export_id in html  # type: ignore[union-attr]
                    or "export" in lowered
                )
            ),
            detail="classification visible",
            category="html",
        ),
        CheckResult(
            name="html:limitations_and_methodology",
            ok="limitation" in lowered and "methodology" in lowered,
            detail="present",
            category="html",
        ),
        CheckResult(
            name="html:no_unsupported_scores",
            ok=not any(frag in lowered for frag in UNSUPPORTED_SCORE_FRAGMENTS),
            detail="honest confidence",
            category="html",
        ),
        CheckResult(
            name="html:print_css",
            ok="@media print" in html and "details" in lowered,
            detail="print + details",
            category="html",
        ),
        CheckResult(
            name="html:no_paths",
            ok="/Users/" not in html and "file://" not in lowered,
            detail="path-free",
            category="html",
        ),
    ]
    return checks
