"""Deterministic WebsiteExportBuildPolicy for commercial static export."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.intelligence_reporting.domain.enums import ReportScope
from codestrata_platform.intelligence_reporting.domain.visibility import (
    WebsiteExportPolicy,
)

WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION = "1.0"
CSP_POLICY_VERSION = "eir-website-csp-v1"
HTML_TEMPLATE_VERSION = "eir-static-html-v2"
JSON_PROJECTION_VERSION = "eir-website-json-v1"
ARTIFACT_TEMPLATE_VERSION = "eir-export-artifacts-v1"

CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'; "
    "img-src data:; "
    "font-src 'none'; "
    "connect-src 'none'; "
    "object-src 'none'; "
    "script-src 'none'; "
    "style-src 'unsafe-inline'"
)


class ExportScope(StrEnum):
    PUBLIC_OSS = "public_oss"
    CUSTOMER_PRIVATE = "customer_private"
    INTERNAL = "internal"
    ANONYMIZED_EXTERNAL = "anonymized_external"


class RepositoryIdentityPolicy(StrEnum):
    PUBLIC_WHEN_PERMITTED = "public_when_permitted"
    ANONYMIZE_ALWAYS = "anonymize_always"
    PRIVATE_DISPLAY_ALLOWED = "private_display_allowed"


def export_scope_for_report_scope(report_scope: ReportScope) -> ExportScope:
    if report_scope is ReportScope.PUBLIC_OSS_DATASET:
        return ExportScope.PUBLIC_OSS
    if report_scope in {
        ReportScope.CUSTOMER_PORTFOLIO,
        ReportScope.CUSTOMER_WORKSPACE,
    }:
        return ExportScope.CUSTOMER_PRIVATE
    if report_scope is ReportScope.INTERNAL_VALIDATION_DATASET:
        return ExportScope.INTERNAL
    return ExportScope.ANONYMIZED_EXTERNAL


@dataclass(frozen=True, slots=True)
class WebsiteExportBuildPolicy:
    """Application export policy — deterministic token for interpretation bundle."""

    policy_id: str = "website-export"
    policy_version: str = "v1"
    export_scope: ExportScope = ExportScope.ANONYMIZED_EXTERNAL
    repository_identity_policy: RepositoryIdentityPolicy = (
        RepositoryIdentityPolicy.ANONYMIZE_ALWAYS
    )
    anonymization_policy: str = "stable_sha8_alias"
    source_reference_policy: str = "omit"
    canonical_report_link_policy: str = "availability_statement_only"
    evidence_reference_policy: str = "omit"
    entity_label_policy: str = "allowlisted_safe_labels"
    maximum_repository_drilldowns: int = 50
    maximum_pattern_items: int = 100
    maximum_observation_items: int = 100
    maximum_capability_rows: int = 50
    maximum_finding_refs_per_drilldown: int = 20
    maximum_recommendation_refs_per_drilldown: int = 20
    include_methodology: bool = True
    include_limitations: bool = True
    include_repository_ids: bool = False
    include_public_source_links: bool = False
    allow_external_assets: bool = False
    csp_policy_version: str = CSP_POLICY_VERSION
    html_template_version: str = HTML_TEMPLATE_VERSION
    json_projection_version: str = JSON_PROJECTION_VERSION
    artifact_template_version: str = ARTIFACT_TEMPLATE_VERSION
    export_schema_version: str = WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION
    domain_visibility_policy: WebsiteExportPolicy | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy_id and policy_version are required")
        if self.allow_external_assets:
            raise ValueError("external assets are prohibited for Slice 6.10")
        for name in (
            "maximum_repository_drilldowns",
            "maximum_pattern_items",
            "maximum_observation_items",
            "maximum_capability_rows",
            "maximum_finding_refs_per_drilldown",
            "maximum_recommendation_refs_per_drilldown",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be >= 1")
        if (
            self.export_scope is ExportScope.PUBLIC_OSS
            and self.repository_identity_policy
            is RepositoryIdentityPolicy.PRIVATE_DISPLAY_ALLOWED
        ):
            raise ValueError("public_oss export cannot allow private display names")
        if self.domain_visibility_policy is None:
            if self.export_scope is ExportScope.PUBLIC_OSS:
                object.__setattr__(
                    self, "domain_visibility_policy", WebsiteExportPolicy.public_default()
                )
            else:
                object.__setattr__(
                    self,
                    "domain_visibility_policy",
                    WebsiteExportPolicy.anonymized_default(),
                )

    @property
    def policy_token(self) -> str:
        return (
            f"{self.policy_id}:{self.policy_version}:"
            f"scope={self.export_scope.value}:"
            f"identity={self.repository_identity_policy.value}:"
            f"json={self.json_projection_version}:"
            f"html={self.html_template_version}:"
            f"csp={self.csp_policy_version}:"
            f"schema={self.export_schema_version}"
        )

    @classmethod
    def for_report_scope(cls, report_scope: ReportScope) -> WebsiteExportBuildPolicy:
        scope = export_scope_for_report_scope(report_scope)
        if scope is ExportScope.PUBLIC_OSS:
            return cls(
                export_scope=scope,
                repository_identity_policy=RepositoryIdentityPolicy.PUBLIC_WHEN_PERMITTED,
                include_repository_ids=False,
            )
        if scope is ExportScope.CUSTOMER_PRIVATE:
            return cls(
                export_scope=scope,
                repository_identity_policy=RepositoryIdentityPolicy.PRIVATE_DISPLAY_ALLOWED,
                include_repository_ids=False,
            )
        if scope is ExportScope.INTERNAL:
            return cls(
                export_scope=scope,
                repository_identity_policy=RepositoryIdentityPolicy.PRIVATE_DISPLAY_ALLOWED,
            )
        return cls(
            export_scope=ExportScope.ANONYMIZED_EXTERNAL,
            repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
        )
