"""Assessment metadata privacy and validation tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.routes import (
    assessment_metadata_request_schema,
)
from codestrata_platform.community_cloud_api.validation.validator import (
    validate_request_body,
)

from .assessment_metadata_helpers import valid_assessment_metadata_body


@pytest.mark.parametrize(
    "forbidden",
    [
        "repository_name",
        "repository_url",
        "organization",
        "email",
        "username",
        "branch",
        "commit",
        "path",
        "findings",
        "recommendations",
        "evidence",
        "priority_actions",
        "roadmap",
        "technologies",
        "dependencies",
        "command_args",
        "exception",
        "stack_trace",
        "prompt",
        "model",
        "token_count",
        "cost",
    ],
)
def test_forbidden_top_level_fields_rejected(forbidden: str) -> None:
    body = valid_assessment_metadata_body()
    body[forbidden] = "x"
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(body)


def test_exact_file_counts_and_repo_identity_shapes_rejected() -> None:
    body = valid_assessment_metadata_body()
    body["repository"] = {**body["repository"], "file_count": 120}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(body)
    body = valid_assessment_metadata_body()
    body["repository"] = {
        **body["repository"],  # type: ignore[dict-item]
        "primary_language": "https://github.com/acme/repo",
    }
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(body)


def test_execution_rejects_exact_duration_and_ai_details() -> None:
    body = valid_assessment_metadata_body()
    body["execution"] = {**body["execution"], "duration_ms": 1200}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(body)
    body = valid_assessment_metadata_body()
    body["execution"] = {**body["execution"], "provider": "openai"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(body)
    body = valid_assessment_metadata_body()
    body["artifacts"] = {**body["artifacts"], "report_path": "/tmp/x"}  # type: ignore[dict-item]
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(body)


def test_api_validation_does_not_echo_forbidden_values() -> None:
    body = valid_assessment_metadata_body()
    body["repository_url"] = "https://github.com/acme/secret-repo"
    result = validate_request_body(
        descriptor=assessment_metadata_request_schema(),
        body=json.dumps(body).encode("utf-8"),
        content_type="application/json",
        route_name="assessment_metadata.ingest",
    )
    assert not result.valid
    blob = json.dumps([err.to_stable_dict() for err in result.errors])
    assert "secret-repo" not in blob
    assert "github.com" not in blob
