"""Request/response models for Community report publishing."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import Field, field_validator

from codestrata_platform.community_cloud_api.reports.policy import (
    ALLOWED_ASSESSMENT_ARTIFACTS,
    ALLOWED_EIR_ARTIFACTS,
    LOGICAL_PORTFOLIO,
    LOGICAL_REPOSITORY,
    MAX_ARTIFACTS_PER_PUBLISH,
    MAX_ARTIFACT_BYTES,
    REPORT_TYPE_ASSESSMENT,
    REPORT_TYPE_EIR,
    VALID_REPORT_TYPES,
)
from codestrata_platform.community_cloud_api.validation.models import (
    CommunityApiRequestModel,
)

_LOGICAL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,120}$")
_ARTIFACT_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,120}$")


class ReportUploadIntentRequest(CommunityApiRequestModel):
    """Authenticated request to stage report artifacts for publish."""

    schema_version: Literal["1.0"] = "1.0"
    report_type: str
    logical_identity_type: str
    logical_identity_key: str
    artifacts: list[str] = Field(min_length=1, max_length=MAX_ARTIFACTS_PER_PUBLISH)
    private_repository_acknowledged: bool = False
    confirm_public_publish: bool = False

    @field_validator("report_type")
    @classmethod
    def _report_type(cls, value: str) -> str:
        text = (value or "").strip()
        if text not in VALID_REPORT_TYPES:
            raise ValueError("unsupported report_type")
        return text

    @field_validator("logical_identity_type")
    @classmethod
    def _logical_type(cls, value: str) -> str:
        text = (value or "").strip()
        if text not in {LOGICAL_REPOSITORY, LOGICAL_PORTFOLIO}:
            raise ValueError("unsupported logical_identity_type")
        return text

    @field_validator("logical_identity_key")
    @classmethod
    def _logical_key(cls, value: str) -> str:
        text = (value or "").strip()
        if not _LOGICAL_ID_RE.fullmatch(text):
            raise ValueError("invalid logical_identity_key")
        return text

    @field_validator("artifacts")
    @classmethod
    def _artifacts(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            name = (item or "").strip()
            if not _ARTIFACT_NAME_RE.fullmatch(name):
                raise ValueError("invalid artifact name")
            if ".." in name or "/" in name or "\\" in name:
                raise ValueError("invalid artifact name")
            cleaned.append(name)
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("duplicate artifact names")
        return cleaned


class ReportPublishRequest(CommunityApiRequestModel):
    """Finalize a staged upload into current/previous cloud lifecycle."""

    schema_version: Literal["1.0"] = "1.0"
    upload_id: str = Field(min_length=16, max_length=64)
    confirm_public_publish: bool = False
    private_repository_acknowledged: bool = False

    @field_validator("upload_id")
    @classmethod
    def _upload_id(cls, value: str) -> str:
        text = (value or "").strip()
        if not re.fullmatch(r"^[A-Za-z0-9_-]{16,64}$", text):
            raise ValueError("invalid upload_id")
        return text


class ReportRevokeRequest(CommunityApiRequestModel):
    """Authenticated revoke body (also supports path public_id)."""

    schema_version: Literal["1.0"] = "1.0"
    public_id: str = Field(min_length=32, max_length=48)


def allowed_artifacts_for(report_type: str) -> frozenset[str]:
    if report_type == REPORT_TYPE_ASSESSMENT:
        return ALLOWED_ASSESSMENT_ARTIFACTS
    if report_type == REPORT_TYPE_EIR:
        return ALLOWED_EIR_ARTIFACTS
    return frozenset()


def validate_artifact_set(report_type: str, artifacts: list[str]) -> None:
    allowed = allowed_artifacts_for(report_type)
    unknown = sorted(set(artifacts) - set(allowed))
    if unknown:
        raise ValueError(f"disallowed artifacts: {unknown}")
    # Prefer bounded html+json pair; require at least html.
    html_names = {n for n in artifacts if n.endswith(".html")}
    if not html_names:
        raise ValueError("html artifact required")


def public_safe_metadata(record: dict[str, Any]) -> dict[str, Any]:
    """Strip private logical identity from public responses."""

    return {
        "generated_at": record.get("generated_at"),
        "public_id": record.get("public_id"),
        "report_type": record.get("report_type"),
        "slot": record.get("slot"),
        "status": record.get("status"),
        "engine_version": record.get("engine_version"),
    }


__all__ = [
    "ReportPublishRequest",
    "ReportRevokeRequest",
    "ReportUploadIntentRequest",
    "allowed_artifacts_for",
    "public_safe_metadata",
    "validate_artifact_set",
    "MAX_ARTIFACT_BYTES",
]
