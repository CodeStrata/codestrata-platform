"""Strict assessment metadata request models (Slice 7.8)."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, field_validator

from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    AssessmentDurationBucket,
    AssessmentExecutionResult,
    AssessmentFailureCategory,
    AssessmentHead,
    AssessmentHeadConfidenceLevel,
    AssessmentMode,
    AssessmentStatus,
    CountBucket,
    FindingAggregateCategory,
    FindingAggregateSeverity,
    PackageEcosystem,
    PrimaryLanguage,
    RepositoryShape,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    default_assessment_metadata_policy,
)
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryClient
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
)
from codestrata_platform.community_cloud_api.validation.sanitization import (
    contains_secret_like_value,
    reject_control_characters,
)
from codestrata_platform.community_cloud_api.validation.schema import (
    ApiClientVersion,
    ApiEventId,
    ApiInstallationId,
    ApiPlatformName,
)

_SCHEMA_VERSION_RE = re.compile(r"^\d+\.\d+$")
_NonNegCount = Annotated[StrictInt, Field(ge=0, le=1_000_000)]
_PositiveCount = Annotated[StrictInt, Field(ge=1, le=1_000_000)]
# Opaque UUID (canonical 8-4-4-4-12 hex) — never repo-timestamp path ids.
_ASSESSMENT_ID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
# Shared Rule Platform + legacy codestrata-rule-* only (Epic 20.4).
_SHARED_RULE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_-]*)+$")
_LEGACY_RULE_ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")
_MAX_FINDING_AGGREGATES = 500
_MAX_HEAD_CONFIDENCE = 16


class AssessmentMetadataBlock(CommunityApiRequestModel):
    """Aggregate assessment facts — no findings, titles, or IDs."""

    assessment_schema_version: StrictStr = Field(min_length=1, max_length=16)
    assessment_status: StrictStr = Field(min_length=1, max_length=32)
    assessment_mode: StrictStr = Field(min_length=1, max_length=32)
    executed_heads: list[StrictStr] = Field(default_factory=list, max_length=16)
    finding_count: _NonNegCount
    recommendation_count: _NonNegCount
    priority_action_count: _NonNegCount
    roadmap_initiative_count: _NonNegCount
    evidence_count: _NonNegCount
    limitation_count: _NonNegCount

    @field_validator("assessment_schema_version")
    @classmethod
    def _schema_version(cls, value: str) -> str:
        text = value.strip()
        if reject_control_characters(text) or any(ch.isspace() for ch in text):
            raise ValueError("unsafe_value")
        if not _SCHEMA_VERSION_RE.fullmatch(text):
            raise ValueError("invalid_format")
        policy = default_assessment_metadata_policy()
        if text not in policy.allowed_assessment_schema_versions:
            raise ValueError("invalid_enum")
        return text

    @field_validator("assessment_status")
    @classmethod
    def _status(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AssessmentStatus}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("assessment_mode")
    @classmethod
    def _mode(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AssessmentMode}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("executed_heads")
    @classmethod
    def _heads(cls, value: list[str]) -> list[str]:
        policy = default_assessment_metadata_policy()
        allowed = set(policy.allowed_heads)
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            text = item.strip()
            if text not in allowed:
                raise ValueError("invalid_enum")
            if text in seen:
                continue  # deterministic normalize: dedupe
            seen.add(text)
            cleaned.append(text)
        if len(cleaned) > policy.maximum_head_count:
            raise ValueError("too_long")
        return sorted(cleaned)


class RepositoryMetadata(CommunityApiRequestModel):
    """Broad anonymous repository characteristics only."""

    primary_language: StrictStr = Field(min_length=1, max_length=32)
    language_count: _NonNegCount
    dependency_ecosystem_count: _NonNegCount
    file_count_bucket: StrictStr = Field(min_length=1, max_length=32)
    source_file_count_bucket: StrictStr = Field(min_length=1, max_length=32)
    test_file_count_bucket: StrictStr = Field(min_length=1, max_length=32)
    repository_shape: StrictStr = Field(min_length=1, max_length=32)
    has_tests: StrictBool
    has_build_files: StrictBool
    has_dependency_manifests: StrictBool
    # Optional additive (Slice 15.4 / CR-15.3-001). Schema 1.0 additive-compatible.
    package_ecosystem: StrictStr | None = Field(default=None, min_length=1, max_length=32)

    @field_validator("primary_language")
    @classmethod
    def _language(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in PrimaryLanguage}:
            raise ValueError("invalid_enum")
        if contains_secret_like_value(text):
            raise ValueError("unsafe_value")
        return text

    @field_validator("package_ecosystem")
    @classmethod
    def _package_ecosystem(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if text not in {item.value for item in PackageEcosystem}:
            raise ValueError("invalid_enum")
        if contains_secret_like_value(text):
            raise ValueError("unsafe_value")
        # Reject values that look like package coordinates / names.
        if any(ch in text for ch in ("/", ":", "@", ".", " ")):
            raise ValueError("invalid_enum")
        return text

    @field_validator(
        "file_count_bucket",
        "source_file_count_bucket",
        "test_file_count_bucket",
    )
    @classmethod
    def _buckets(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in CountBucket}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("repository_shape")
    @classmethod
    def _shape(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in RepositoryShape}:
            raise ValueError("invalid_enum")
        return text


class AssessmentExecutionMetadata(CommunityApiRequestModel):
    """Anonymous execution facts — no args, paths, or AI details beyond boolean."""

    duration_bucket: StrictStr = Field(min_length=1, max_length=32)
    result: StrictStr = Field(min_length=1, max_length=32)
    ai_used: StrictBool
    offline_mode: StrictBool
    client_version: ApiClientVersion
    platform: ApiPlatformName
    # Additive assessment_metadata 1.1 (optional on 1.0 payloads).
    failure_category: StrictStr | None = Field(default=None, min_length=1, max_length=32)

    @field_validator("duration_bucket")
    @classmethod
    def _duration(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AssessmentDurationBucket}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("result")
    @classmethod
    def _result(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AssessmentExecutionResult}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("failure_category")
    @classmethod
    def _failure_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        if text not in {item.value for item in AssessmentFailureCategory}:
            raise ValueError("invalid_enum")
        return text


class FindingAggregateRow(CommunityApiRequestModel):
    """One privacy-safe finding aggregate row (assessment_metadata 1.1)."""

    rule_id: StrictStr = Field(min_length=1, max_length=128)
    severity: StrictStr = Field(min_length=1, max_length=32)
    category: StrictStr = Field(min_length=1, max_length=32)
    count: _PositiveCount

    @field_validator("rule_id")
    @classmethod
    def _rule_id(cls, value: str) -> str:
        text = value.strip().lower()
        if reject_control_characters(text) or any(ch.isspace() for ch in text):
            raise ValueError("unsafe_value")
        if text.startswith("pmd.") or text.startswith("provider:"):
            raise ValueError("invalid_enum")
        if not (
            _SHARED_RULE_ID_RE.fullmatch(text) or _LEGACY_RULE_ID_RE.fullmatch(text)
        ):
            raise ValueError("invalid_format")
        if contains_secret_like_value(text):
            raise ValueError("unsafe_value")
        return text

    @field_validator("severity")
    @classmethod
    def _severity(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in FindingAggregateSeverity}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("category")
    @classmethod
    def _category(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in FindingAggregateCategory}:
            raise ValueError("invalid_enum")
        return text


class HeadConfidenceRow(CommunityApiRequestModel):
    """Per-head confidence (assessment_metadata 1.1)."""

    head: StrictStr = Field(min_length=1, max_length=32)
    confidence_level: StrictStr = Field(min_length=1, max_length=32)

    @field_validator("head")
    @classmethod
    def _head(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AssessmentHead}:
            raise ValueError("invalid_enum")
        return text

    @field_validator("confidence_level")
    @classmethod
    def _level(cls, value: str) -> str:
        text = value.strip()
        if text not in {item.value for item in AssessmentHeadConfidenceLevel}:
            raise ValueError("invalid_enum")
        return text


class AssessmentArtifactMetadata(CommunityApiRequestModel):
    """Artifact generation flags only — no paths, digests, or contents."""

    report_json_generated: StrictBool
    findings_json_generated: StrictBool
    recommendations_json_generated: StrictBool
    html_report_generated: StrictBool
    artifact_count: Annotated[StrictInt, Field(ge=0, le=100)]


class AssessmentMetadataRequest(CommunityApiRequestModel):
    """Privacy-first assessment metadata envelope (1.0 and additive 1.1)."""

    schema_version: Literal["1.0", "1.1"]  # type: ignore[valid-type]
    event_id: ApiEventId
    client: TelemetryClient
    installation_id: ApiInstallationId | None = None
    # Required when schema_version == "1.1"; omitted on legacy 1.0 clients.
    assessment_id: StrictStr | None = Field(default=None, min_length=1, max_length=64)
    assessment: AssessmentMetadataBlock
    repository: RepositoryMetadata
    execution: AssessmentExecutionMetadata
    artifacts: AssessmentArtifactMetadata
    finding_aggregates: list[FindingAggregateRow] = Field(default_factory=list)
    head_confidence: list[HeadConfidenceRow] = Field(default_factory=list)

    @field_validator("assessment_id")
    @classmethod
    def _assessment_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip().lower()
        if reject_control_characters(text) or any(ch.isspace() for ch in text):
            raise ValueError("unsafe_value")
        if not _ASSESSMENT_ID_RE.fullmatch(text):
            raise ValueError("invalid_format")
        if contains_secret_like_value(text):
            raise ValueError("unsafe_value")
        return text

    @field_validator("finding_aggregates")
    @classmethod
    def _finding_aggregates(
        cls, value: list[FindingAggregateRow]
    ) -> list[FindingAggregateRow]:
        if len(value) > _MAX_FINDING_AGGREGATES:
            raise ValueError("too_long")
        # Deterministic order for stable fingerprints.
        return sorted(
            value,
            key=lambda row: (row.rule_id, row.severity, row.category, row.count),
        )

    @field_validator("head_confidence")
    @classmethod
    def _head_confidence(cls, value: list[HeadConfidenceRow]) -> list[HeadConfidenceRow]:
        if len(value) > _MAX_HEAD_CONFIDENCE:
            raise ValueError("too_long")
        seen: set[str] = set()
        cleaned: list[HeadConfidenceRow] = []
        for row in sorted(value, key=lambda item: item.head):
            if row.head in seen:
                continue
            seen.add(row.head)
            cleaned.append(row)
        return cleaned

    def fingerprint_payload(self) -> dict[str, Any]:
        """Material for payload fingerprinting.

        Includes ``event_id`` (Slice 7.7 decision). No timestamps in this schema.
        Transport ``request_id`` is never present on this model.
        """

        return self.to_stable_dict()

    def schema_version_value(self) -> str:
        return str(self.schema_version)
