"""Assessment metadata request model tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.assessment_metadata.enums import AssessmentHead
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_POLICY_URN,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    CommunityAssessmentMetadataPolicy,
)

from .assessment_metadata_helpers import valid_assessment_metadata_body


def test_required_blocks_and_schema() -> None:
    model = AssessmentMetadataRequest.model_validate(valid_assessment_metadata_body())
    assert model.schema_version == COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION
    assert model.event_id == "amd-test-0001"
    assert model.assessment.assessment_schema_version == "1.2"
    assert model.repository.primary_language == "python"
    assert model.execution.ai_used is False
    assert model.artifacts.report_json_generated is True


def test_immutable_unknown_fields_and_array_rejected() -> None:
    model = AssessmentMetadataRequest.model_validate(valid_assessment_metadata_body())
    with pytest.raises(ValidationError):
        model.event_id = "other"  # type: ignore[misc]
    bad = valid_assessment_metadata_body()
    bad["extra"] = True
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(bad)
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate([valid_assessment_metadata_body()])


def test_heads_deduped_sorted_unknown_rejected() -> None:
    body = valid_assessment_metadata_body()
    body["assessment"] = {
        **body["assessment"],  # type: ignore[dict-item]
        "executed_heads": ["security", "technology_inventory", "security"],
    }
    model = AssessmentMetadataRequest.model_validate(body)
    assert model.assessment.executed_heads == ["security", "technology_inventory"]
    for head in AssessmentHead:
        body2 = valid_assessment_metadata_body()
        body2["assessment"] = {
            **body2["assessment"],  # type: ignore[dict-item]
            "executed_heads": [head.value],
        }
        AssessmentMetadataRequest.model_validate(body2)
    body3 = valid_assessment_metadata_body()
    body3["assessment"] = {
        **body3["assessment"],  # type: ignore[dict-item]
        "executed_heads": ["engineering_intelligence"],
    }
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(body3)


def test_counts_and_status_vocab() -> None:
    with pytest.raises(ValidationError):
        body = valid_assessment_metadata_body()
        body["assessment"] = {**body["assessment"], "finding_count": -1}  # type: ignore[dict-item]
        AssessmentMetadataRequest.model_validate(body)
    with pytest.raises(ValidationError):
        body = valid_assessment_metadata_body()
        body["assessment"] = {**body["assessment"], "finding_count": "3"}  # type: ignore[dict-item]
        AssessmentMetadataRequest.model_validate(body)
    with pytest.raises(ValidationError):
        body = valid_assessment_metadata_body()
        body["assessment"] = {**body["assessment"], "assessment_status": "ok"}  # type: ignore[dict-item]
        AssessmentMetadataRequest.model_validate(body)
    with pytest.raises(ValidationError):
        body = valid_assessment_metadata_body()
        body["assessment"] = {
            **body["assessment"],  # type: ignore[dict-item]
            "assessment_schema_version": "9.9",
        }
        AssessmentMetadataRequest.model_validate(body)


def test_policy_token_stable() -> None:
    policy = CommunityAssessmentMetadataPolicy.default()
    assert policy.policy_token == COMMUNITY_ASSESSMENT_METADATA_POLICY_URN
    assert policy.to_stable_dict() == CommunityAssessmentMetadataPolicy.default().to_stable_dict()
    with pytest.raises(ValueError):
        CommunityAssessmentMetadataPolicy(policy_version="9.9")
