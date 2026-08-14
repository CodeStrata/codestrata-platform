"""Slice 20.7 — assessment_metadata schema 1.0 + additive 1.1 API acceptance."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.assessment_metadata.policy import (
    COMMUNITY_ASSESSMENT_METADATA_LATEST_SCHEMA_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION,
    COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS,
    default_assessment_metadata_policy,
)
from codestrata_platform.community_cloud_api.assessment_metadata.validation import (
    validate_assessment_metadata_semantics,
)

from .assessment_metadata_helpers import (
    configured_metadata_client,
    valid_assessment_metadata_body,
)

_AID = "11111111-2222-3333-4444-555555555555"


def _valid_1_1(**overrides: object) -> dict[str, object]:
    body = valid_assessment_metadata_body(
        schema_version="1.1",
        assessment_id=_AID,
        finding_aggregates=[
            {
                "rule_id": "architecture.layer-dependency",
                "severity": "high",
                "category": "architecture",
                "count": 3,
            }
        ],
        head_confidence=[{"head": "security", "confidence_level": "moderate"}],
    )
    body.update(overrides)
    return body


def test_policy_supports_1_0_and_1_1_without_obsoleting_baseline() -> None:
    policy = default_assessment_metadata_policy()
    assert COMMUNITY_ASSESSMENT_METADATA_SCHEMA_VERSION == "1.0"
    assert COMMUNITY_ASSESSMENT_METADATA_LATEST_SCHEMA_VERSION == "1.1"
    assert COMMUNITY_ASSESSMENT_METADATA_SUPPORTED_SCHEMA_VERSIONS == {"1.0", "1.1"}
    assert set(policy.supported_schema_versions) == {"1.0", "1.1"}
    assert policy.schema_version == "1.0"


def test_a1_valid_1_0_accepted_unchanged() -> None:
    client, sink, *_ = configured_metadata_client()
    response = client.post("/api/v1/assessment-metadata", json=valid_assessment_metadata_body())
    assert response.status_code in {200, 202}
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.schema_version == "1.0"
    assert event.assessment_id is None
    assert event.finding_aggregates == ()
    assert event.head_confidence == ()


def test_a2_valid_1_1_accepted() -> None:
    client, sink, *_ = configured_metadata_client()
    body = _valid_1_1()
    body["execution"] = {
        "duration_bucket": "10s_to_30s",
        "result": "succeeded",
        "ai_used": False,
        "offline_mode": True,
        "client_version": "0.2.1",
        "platform": "darwin",
        "failure_category": "validation",
    }
    response = client.post("/api/v1/assessment-metadata", json=body)
    assert response.status_code in {200, 202}, response.text
    assert len(sink.events) == 1
    event = sink.events[0]
    assert event.schema_version == "1.1"
    assert event.assessment_id == _AID
    assert len(event.finding_aggregates) == 1
    assert event.finding_aggregates[0].rule_id == "architecture.layer-dependency"
    assert event.head_confidence[0].confidence_level == "moderate"
    assert event.execution.failure_category == "validation"


def test_a3_aggregate_findings_validated() -> None:
    body = _valid_1_1(
        finding_aggregates=[
            {
                "rule_id": "architecture.layer-dependency",
                "severity": "medium",
                "category": "architecture",
                "count": 1,
            }
        ]
    )
    model = AssessmentMetadataRequest.model_validate(body)
    assert validate_assessment_metadata_semantics(model) == ()


def test_a4_forbidden_unknown_fields_rejected() -> None:
    for field_name, value in (
        ("repository_name", "VERY_PRIVATE_REPO_123"),
        ("repository_url", "https://internal.acme.example/private"),
        ("path", "/Users/private/AcmeSecretProject/payments/"),
        ("source", "AcmeInternalSettlementEngine"),
        ("evidence", "TEST_SECRET_DO_NOT_TRANSMIT"),
        ("snippet", "secret snippet"),
        ("report_url", "https://internal.acme.example/r"),
        ("report_id", "rpt-secret"),
        ("stack_trace", "traceback"),
        ("graph", {"nodes": []}),
        ("dependencies", ["acme-internal-payments-sdk"]),
    ):
        body = _valid_1_1()
        body[field_name] = value
        with pytest.raises(ValidationError):
            AssessmentMetadataRequest.model_validate(body)


def test_a5_invalid_enum_rejected() -> None:
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(
            _valid_1_1(head_confidence=[{"head": "security", "confidence_level": "excellent"}])
        )


def test_a6_invalid_assessment_id_rejected() -> None:
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(
            _valid_1_1(assessment_id="my-repo-20260812-120000")
        )


def test_a7_invalid_counts_rejected() -> None:
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(
            _valid_1_1(
                finding_aggregates=[
                    {
                        "rule_id": "architecture.layer-dependency",
                        "severity": "high",
                        "category": "architecture",
                        "count": 0,
                    }
                ]
            )
        )


def test_a8_unsupported_schema_version_rejected() -> None:
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(
            valid_assessment_metadata_body(schema_version="9.9")
        )


def test_a9_unsafe_pmd_and_provider_rule_ids_rejected() -> None:
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(
            _valid_1_1(
                finding_aggregates=[
                    {
                        "rule_id": "PMD.JAVA.BestPractices.Foo",
                        "severity": "low",
                        "category": "maintainability",
                        "count": 1,
                    }
                ]
            )
        )
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(
            _valid_1_1(
                finding_aggregates=[
                    {
                        "rule_id": "provider:openai",
                        "severity": "low",
                        "category": "unknown",
                        "count": 1,
                    }
                ]
            )
        )
    with pytest.raises(ValidationError):
        AssessmentMetadataRequest.model_validate(
            _valid_1_1(
                finding_aggregates=[
                    {
                        "rule_id": "git@github.com:private/acme-secret.git",
                        "severity": "low",
                        "category": "unknown",
                        "count": 1,
                    }
                ]
            )
        )


def test_a10_empty_optional_aggregates_accepted() -> None:
    body = valid_assessment_metadata_body(
        schema_version="1.1",
        assessment_id=_AID,
        finding_aggregates=[],
        head_confidence=[],
    )
    model = AssessmentMetadataRequest.model_validate(body)
    assert validate_assessment_metadata_semantics(model) == ()
    assert model.finding_aggregates == []
    assert model.head_confidence == []


def test_1_0_payload_cannot_carry_1_1_fields() -> None:
    model = AssessmentMetadataRequest.model_validate(
        valid_assessment_metadata_body(assessment_id=_AID)
    )
    errors = validate_assessment_metadata_semantics(model)
    assert any(err.field == "assessment_id" for err in errors)


def test_valid_shared_rule_id_accepted() -> None:
    model = AssessmentMetadataRequest.model_validate(
        _valid_1_1(
            finding_aggregates=[
                {
                    "rule_id": "maintainability.long-method",
                    "severity": "medium",
                    "category": "maintainability",
                    "count": 2,
                }
            ]
        )
    )
    assert model.finding_aggregates[0].rule_id == "maintainability.long-method"


def test_privacy_canary_api_rejects_and_does_not_persist() -> None:
    client, sink, *_ = configured_metadata_client()
    canaries = (
        "VERY_PRIVATE_REPO_123",
        "/Users/private/AcmeSecretProject/payments/",
        "AcmeInternalSettlementEngine",
        "TEST_SECRET_DO_NOT_TRANSMIT",
        "git@github.com:private/acme-secret.git",
        "acme-internal-payments-sdk",
        "https://internal.acme.example/private",
    )
    for value in canaries:
        body = _valid_1_1()
        body["repository_name"] = value
        response = client.post("/api/v1/assessment-metadata", json=body)
        assert response.status_code in {400, 422}, value
        assert sink.events == []
        # Response must not echo the forbidden value.
        assert value not in response.text
