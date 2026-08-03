"""Fail-closed validation for website-safe export projection and artifacts."""

from __future__ import annotations

import re

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.website_export.models import (
    WebsiteSafeExportDocument,
)
from codestrata_platform.intelligence_reporting.application.website_export.policy import (
    ExportScope,
    WebsiteExportBuildPolicy,
)

_UNSAFE_HTML_MARKERS = (
    "<script",
    "javascript:",
    "onerror=",
    "onload=",
    "onclick=",
    "<iframe",
    "<object",
    "<embed",
    "<form",
    "http-equiv=\"refresh\"",
)

_PATH_MARKERS = (
    "/users/",
    "/home/",
    "/tmp/",
    "/private/",
    "file://",
    "\\users\\",
)


def validate_website_safe_document(
    document: WebsiteSafeExportDocument,
    *,
    policy: WebsiteExportBuildPolicy,
) -> None:
    if document.export_schema_version != policy.export_schema_version:
        raise InvalidValueError(
            "export schema version mismatch",
            reason_code="export_schema_mismatch",
        )
    if document.scope != policy.export_scope.value:
        raise InvalidValueError(
            "document scope does not match export policy",
            reason_code="export_scope_document_mismatch",
        )
    if document.export_metadata is None:
        raise InvalidValueError(
            "export metadata required",
            reason_code="missing_export_metadata",
        )
    if document.export_metadata.export_policy_id != policy.policy_token:
        raise InvalidValueError(
            "export metadata policy token mismatch",
            reason_code="export_policy_token_mismatch",
        )
    if document.confidence is None:
        raise InvalidValueError(
            "confidence block required",
            reason_code="missing_export_confidence",
        )
    if "accuracy percentage" not in document.confidence.disclaimer.lower():
        raise InvalidValueError(
            "confidence disclaimer missing",
            reason_code="missing_confidence_disclaimer",
        )

    blob = _document_blob(document)
    for marker in _PATH_MARKERS:
        if marker in blob.lower():
            raise InvalidValueError(
                f"unsafe path marker in export: {marker}",
                reason_code="export_unsafe_path",
            )
    if "-----begin" in blob.lower() or "akia" in blob.lower():
        raise InvalidValueError(
            "secret-like content in export",
            reason_code="export_secret_like",
        )
    for marker in _UNSAFE_HTML_MARKERS:
        if marker in blob.lower():
            raise InvalidValueError(
                f"unsafe HTML/script marker in export projection: {marker}",
                reason_code="export_unsafe_html_marker",
            )

    # Counts reconcile with dataset summary.
    summary = document.dataset_summary
    if int(summary.get("pattern_count", -1)) != len(document.recurring_patterns):
        raise InvalidValueError(
            "pattern count mismatch",
            reason_code="export_pattern_count_mismatch",
        )
    if int(summary.get("observation_count", -1)) != len(
        document.modernization_observations
    ):
        raise InvalidValueError(
            "observation count mismatch",
            reason_code="export_observation_count_mismatch",
        )
    if int(summary.get("drilldown_count", -1)) != len(document.repository_drilldowns):
        raise InvalidValueError(
            "drilldown count mismatch",
            reason_code="export_drilldown_count_mismatch",
        )

    if policy.export_scope in {
        ExportScope.CUSTOMER_PRIVATE,
        ExportScope.INTERNAL,
    }:
        if "not for public" not in document.classification.lower():
            raise InvalidValueError(
                "private/internal export must be labeled non-public",
                reason_code="missing_nonpublic_classification",
            )


def validate_html_artifact(html: str) -> None:
    lowered = html.lower()
    if "<!doctype html>" not in lowered:
        raise InvalidValueError(
            "HTML must be HTML5",
            reason_code="html_not_html5",
        )
    if lowered.count("<h1") != 1:
        raise InvalidValueError(
            "HTML must contain exactly one h1",
            reason_code="html_h1_count",
        )
    if "<main" not in lowered:
        raise InvalidValueError("HTML missing main landmark", reason_code="html_missing_main")
    if 'aria-label="table of contents"' not in lowered:
        raise InvalidValueError("HTML missing TOC nav", reason_code="html_missing_toc")
    if "content-security-policy" not in lowered:
        raise InvalidValueError("HTML missing CSP", reason_code="html_missing_csp")
    forbidden = (
        "<script",
        "<iframe",
        "<object",
        "<embed",
        "<form",
        'rel="stylesheet" href="http',
        "src=\"http",
        "javascript:",
        "onerror=",
        "onload=",
        "onclick=",
    )
    for token in forbidden:
        if token in lowered:
            raise InvalidValueError(
                f"HTML contains forbidden construct: {token}",
                reason_code="html_forbidden_construct",
            )
    # Unique ids
    ids = re.findall(r'\bid="([^"]+)"', html)
    if len(ids) != len(set(ids)):
        raise InvalidValueError(
            "duplicate HTML ids",
            reason_code="html_duplicate_ids",
        )
    # Anchors resolve
    hrefs = re.findall(r'href="#([^"]+)"', html)
    id_set = set(ids)
    unresolved = [item for item in hrefs if item not in id_set]
    if unresolved:
        raise InvalidValueError(
            f"unresolved HTML anchors: {unresolved[:5]}",
            reason_code="html_unresolved_anchors",
        )


def _document_blob(document: WebsiteSafeExportDocument) -> str:
    from codestrata_platform.intelligence_reporting.application.website_export.projection import (
        export_document_to_stable_dict,
    )
    import json

    return json.dumps(export_document_to_stable_dict(document), ensure_ascii=True)
