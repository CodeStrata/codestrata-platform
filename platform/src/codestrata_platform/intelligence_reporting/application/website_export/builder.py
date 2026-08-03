"""Orchestrate website-safe projection → JSON → HTML → manifest."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.application.website_export.diagnostics import (
    WebsiteExportDiagnostics,
)
from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
    WebsiteExportManifest,
    build_manifest,
)
from codestrata_platform.intelligence_reporting.application.website_export.models import (
    WebsiteSafeExportDocument,
)
from codestrata_platform.intelligence_reporting.application.website_export.policy import (
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
)
from codestrata_platform.intelligence_reporting.application.website_export.projection import (
    export_document_to_stable_dict,
    project_website_safe_export,
)
from codestrata_platform.intelligence_reporting.application.website_export.validation import (
    validate_html_artifact,
    validate_website_safe_document,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)
from codestrata_platform.intelligence_reporting.presentation.static_html.renderer import (
    render_website_safe_html,
)


JSON_FILENAME = "engineering-intelligence-report.json"
HTML_FILENAME = "engineering-intelligence-report.html"
MANIFEST_FILENAME = "export-manifest.json"


@dataclass(frozen=True, slots=True)
class WebsiteExportBundle:
    """In-memory website-safe export artifacts sharing one projection."""

    document: WebsiteSafeExportDocument
    json_bytes: bytes
    html_bytes: bytes
    manifest: WebsiteExportManifest
    manifest_bytes: bytes
    diagnostics: WebsiteExportDiagnostics
    policy: WebsiteExportBuildPolicy


def serialize_website_safe_json(document: WebsiteSafeExportDocument) -> bytes:
    payload = export_document_to_stable_dict(document)
    return (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def build_website_safe_export(
    report: EngineeringIntelligenceReport,
    *,
    policy: WebsiteExportBuildPolicy | None = None,
    generated_at: str | None = None,
) -> WebsiteExportBundle:
    """Build website-safe JSON/HTML/manifest from an EngineeringIntelligenceReport."""

    active = policy or WebsiteExportBuildPolicy.for_report_scope(report.report_scope)
    document = project_website_safe_export(
        report, policy=active, generated_at=generated_at
    )
    validate_website_safe_document(document, policy=active)

    json_bytes = serialize_website_safe_json(document)
    html = render_website_safe_html(document)
    validate_html_artifact(html)
    html_bytes = html.encode("utf-8")

    metadata = document.export_metadata
    assert metadata is not None
    manifest, manifest_bytes = build_manifest(
        export_id=metadata.export_id,
        export_schema_version=document.export_schema_version,
        source_report_id=document.report_id,
        interpretation_policy_bundle_id=metadata.interpretation_policy_bundle_id,
        export_policy_id=active.policy_token,
        classification=document.classification,
        repository_count=int(document.dataset_summary.get("repository_count", 0)),
        json_bytes=json_bytes,
        html_bytes=html_bytes,
        generated_at=generated_at,
        limitations=document.export_limitations,
    )

    diagnostics = _build_diagnostics(
        report,
        document=document,
        policy=active,
        json_bytes=json_bytes,
        html_bytes=html_bytes,
        html=html,
    )
    return WebsiteExportBundle(
        document=document,
        json_bytes=json_bytes,
        html_bytes=html_bytes,
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        diagnostics=diagnostics,
        policy=active,
    )


def _build_diagnostics(
    report: EngineeringIntelligenceReport,
    *,
    document: WebsiteSafeExportDocument,
    policy: WebsiteExportBuildPolicy,
    json_bytes: bytes,
    html_bytes: bytes,
    html: str,
) -> WebsiteExportDiagnostics:
    included = len(report.dataset.included_repository_ids)
    exported = len(document.repository_drilldowns)
    anonymized = 0
    if policy.repository_identity_policy is RepositoryIdentityPolicy.ANONYMIZE_ALWAYS:
        anonymized = len(document.repository_population)
    elif policy.export_scope in {
        ExportScope.PUBLIC_OSS,
        ExportScope.ANONYMIZED_EXTERNAL,
    }:
        anonymized = sum(
            1
            for alias, _ in document.repository_population
            if alias.startswith("repository-")
        )
    entity_refs = sum(
        len(item.finding_refs) + len(item.recommendation_refs)
        for item in document.repository_drilldowns
    )
    ids = re.findall(r'\bid="([^"]+)"', html)
    hrefs = re.findall(r'href="#([^"]+)"', html)
    unresolved = sum(1 for item in hrefs if item not in set(ids))
    truncation = sum(
        1 for item in document.repository_drilldowns if item.truncation_note
    )
    section_count = sum(
        1
        for present in (
            True,  # scope
            True,  # orientation
            True,  # summary
            bool(document.technology_distribution),
            bool(document.capability_comparisons),
            bool(document.assessment_head_distributions),
            True,  # patterns (may be empty-state)
            True,  # observations
            document.confidence is not None,
            bool(document.limitations) or policy.include_limitations,
            True,  # drilldowns
            document.methodology is not None,
            document.export_metadata is not None,
        )
        if present
    )
    return WebsiteExportDiagnostics(
        repository_count=included,
        exported_repository_count=exported,
        anonymized_repository_count=anonymized,
        omitted_repository_count=max(0, included - len(document.repository_population)),
        section_count=section_count,
        entity_ref_count=entity_refs,
        json_byte_count=len(json_bytes),
        html_byte_count=len(html_bytes),
        anchor_count=len(hrefs),
        unresolved_anchor_count=unresolved,
        unsafe_value_count=0,
        rejected_field_count=0,
        truncation_count=truncation,
        export_id=document.export_metadata.export_id if document.export_metadata else "",
        policy_bundle_id=(
            document.export_metadata.interpretation_policy_bundle_id
            if document.export_metadata
            else ""
        ),
        limitations=document.export_limitations,
    )
