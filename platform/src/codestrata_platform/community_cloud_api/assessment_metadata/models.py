"""Strict assessment metadata request models (Slice 7.8)."""

from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, field_validator

from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
    AssessmentDurationBucket,
    AssessmentExecutionResult,
    AssessmentHead,
    AssessmentMode,
    AssessmentStatus,
    CountBucket,
    PackageEcosystem,
    PrimaryLanguage,
    RepositoryShape,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
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


class AssessmentArtifactMetadata(CommunityApiRequestModel):
    """Artifact generation flags only — no paths, digests, or contents."""

    report_json_generated: StrictBool
    findings_json_generated: StrictBool
    recommendations_json_generated: StrictBool
    html_report_generated: StrictBool
    artifact_count: Annotated[StrictInt, Field(ge=0, le=100)]


class AssessmentMetadataRequest(CommunityApiRequestModel):
    """Privacy-first assessment metadata envelope."""

    schema_version: Literal["1.0"]  # type: ignore[valid-type]
    event_id: ApiEventId
    client: TelemetryClient
    installation_id: ApiInstallationId | None = None
    assessment: AssessmentMetadataBlock
    repository: RepositoryMetadata
    execution: AssessmentExecutionMetadata
    artifacts: AssessmentArtifactMetadata

    def fingerprint_payload(self) -> dict[str, Any]:
        """Material for payload fingerprinting.

        Includes ``event_id`` (Slice 7.7 decision). No timestamps in this schema.
        Transport ``request_id`` is never present on this model.
        """

        return self.to_stable_dict()

    def schema_version_value(self) -> str:
        return COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION
