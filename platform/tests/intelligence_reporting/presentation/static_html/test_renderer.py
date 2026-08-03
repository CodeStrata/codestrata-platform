"""Static HTML renderer tests for website-safe EIR export."""

from __future__ import annotations

import re

from codestrata_platform.intelligence_reporting.application.website_export import (
    CONTENT_SECURITY_POLICY,
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
)
from codestrata_platform.intelligence_reporting.presentation.static_html.validation import (
    validate_html_artifact,
)
from tests.intelligence_reporting.application.website_export.conftest import prepare_export


def _bundle():
    return prepare_export(
        export_policy=WebsiteExportBuildPolicy(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
    )[4]


def test_html5_landmarks_csp_and_no_scripts() -> None:
    bundle = _bundle()
    html = bundle.html_bytes.decode("utf-8")
    validate_html_artifact(html)
    lowered = html.lower()
    assert "<!doctype html>" in lowered
    assert lowered.count("<h1") == 1
    assert "<main" in lowered
    assert 'aria-label="table of contents"' in lowered
    assert "skip to main content" in lowered
    assert CONTENT_SECURITY_POLICY in html
    assert "<script" not in lowered
    assert "<form" not in lowered
    assert "<iframe" not in lowered
    assert 'rel="stylesheet"' not in lowered
    assert "@media print" in html
    assert "<style>" in lowered


def test_anchors_unique_and_resolve() -> None:
    bundle = _bundle()
    html = bundle.html_bytes.decode("utf-8")
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    hrefs = re.findall(r'href="#([^"]+)"', html)
    assert hrefs
    assert set(hrefs).issubset(set(ids))


def test_html_escaping() -> None:
    from codestrata_platform.intelligence_reporting.presentation.static_html.renderer import (
        escape,
    )

    assert escape('<script>alert("x")</script>') == (
        "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
    )


def test_json_html_parity() -> None:
    bundle = _bundle()
    doc = bundle.document
    html = bundle.html_bytes.decode("utf-8")
    assert doc.report_id in html
    assert str(doc.dataset_summary["repository_count"]) in html
    assert str(len(doc.recurring_patterns)) in html or "recurring patterns" in html.lower()
    if doc.confidence:
        assert doc.confidence.level in html
    assert str(len(doc.limitations)) in html or "limitations" in html.lower()
    assert len(doc.repository_drilldowns) == int(doc.dataset_summary["drilldown_count"])
    for item in doc.repository_drilldowns:
        assert item.repository_alias in html
