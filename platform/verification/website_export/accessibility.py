"""Accessibility structure verification."""

from __future__ import annotations

import re

from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_accessibility(verified: VerifiedExportInput) -> list[CheckResult]:
    html = verified.bundle.html_bytes.decode("utf-8")
    lowered = html.lower()
    ids = re.findall(r'\bid="([^"]+)"', html)
    empty_links = re.findall(r"<a\b[^>]*>\s*</a>", html, flags=re.I)
    tables_without_th = 0
    for match in re.finditer(r"<table\b[^>]*>(.*?)</table>", html, flags=re.I | re.S):
        if "<th" not in match.group(1).lower():
            tables_without_th += 1
    details_ok = True
    for match in re.finditer(r"<details\b[^>]*>(.*?)</details>", html, flags=re.I | re.S):
        if "<summary" not in match.group(1).lower():
            details_ok = False
            break
    return [
        CheckResult(
            name="a11y:one_h1",
            ok=lowered.count("<h1") == 1,
            detail=f"h1={lowered.count('<h1')}",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:main_landmark",
            ok="<main" in lowered,
            detail="main",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:toc_nav",
            ok='aria-label="table of contents"' in lowered,
            detail="nav toc",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:skip_link",
            ok="skip to main content" in lowered,
            detail="skip link",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:unique_ids",
            ok=len(ids) == len(set(ids)),
            detail=f"ids={len(ids)}",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:no_empty_links",
            ok=len(empty_links) == 0,
            detail=f"empty={len(empty_links)}",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:tables_have_headers",
            ok=tables_without_th == 0,
            detail=f"missing_th={tables_without_th}",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:details_have_summary",
            ok=details_ok,
            detail="details/summary",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:classification_text",
            ok=verified.bundle.document.classification in html,
            detail="text classification",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:confidence_text",
            ok=(
                verified.bundle.document.confidence is not None
                and verified.bundle.document.confidence.level in html
            ),
            detail="confidence text",
            category="accessibility",
        ),
        CheckResult(
            name="a11y:print_expands_details",
            ok="@media print" in html and "details" in lowered,
            detail="print CSS present",
            category="accessibility",
        ),
    ]
