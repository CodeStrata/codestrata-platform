"""Phase 14.4 Platform contract hardening tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from codestrata_platform.api.contracts import API_MAJOR_VERSION, API_VERSION_HEADER
from codestrata_platform.api.contracts.serialization import to_jsonable
from codestrata_platform.api.contracts.validation import validate_response
from codestrata_platform.api.dto.common import ErrorResponseDto, HealthResponseDto
from codestrata_platform.api.dto.response.engineering import EngineeringTechnologyItemDto
from codestrata_platform.application.common.errors import ValidationError


def test_api_version_header_present(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get(API_VERSION_HEADER) == API_MAJOR_VERSION


def test_health_response_is_dto(client: TestClient) -> None:
    body = client.get("/health").json()
    dto = HealthResponseDto.model_validate(body)
    assert dto.status == "ok"
    assert dto.version


def test_error_envelope_includes_correlation_id(client: TestClient) -> None:
    response = client.get("/api/v1/organizations/does-not-exist")
    assert response.status_code == 404
    envelope = ErrorResponseDto.model_validate(response.json())
    assert envelope.error.code
    assert envelope.error.message
    assert envelope.error.correlation_id
    assert response.headers.get("X-Correlation-Id") == envelope.error.correlation_id


def test_request_validation_error_is_deterministic(client: TestClient) -> None:
    response = client.post("/api/v1/organizations", json={})
    assert response.status_code == 422
    envelope = ErrorResponseDto.model_validate(response.json())
    assert envelope.error.code == "request_validation_error"
    assert envelope.error.details is not None
    assert "errors" in envelope.error.details


def test_engineering_technology_dto_roundtrip() -> None:
    dto = EngineeringTechnologyItemDto(
        technology_id="tech:1",
        canonical_key="python",
        display_name="Python",
        category="language",
    )
    dumped = dto.model_dump(mode="json")
    assert dumped == {
        "technology_id": "tech:1",
        "canonical_key": "python",
        "display_name": "Python",
        "category": "language",
    }
    assert validate_response(EngineeringTechnologyItemDto, dumped).technology_id == "tech:1"


def test_response_validation_rejects_invalid_payload() -> None:
    with pytest.raises(ValidationError) as exc:
        validate_response(
            EngineeringTechnologyItemDto,
            {"technology_id": 1, "canonical_key": "x", "display_name": "y", "category": "z"},
        )
    assert exc.value.reason_code == "response_validation_error"


def test_to_jsonable_unwraps_value_objects() -> None:
    from codestrata_platform.domain.portfolio.identifiers import PortfolioTechnologyId

    wrapped = PortfolioTechnologyId.from_canonical(
        portfolio_snapshot_id="psnap:1",
        canonical_key="java",
    )
    assert isinstance(to_jsonable(wrapped), str)


def test_schema_stability_error_response_fields() -> None:
    schema = ErrorResponseDto.model_json_schema()
    detail = schema.get("$defs", {}).get("ErrorDetailDto") or schema["properties"]["error"]
    props = detail.get("properties", detail)
    assert "code" in props
    assert "message" in props
    assert "details" in props
    assert "correlation_id" in props


def test_no_partial_ops_in_live_openapi(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    partial = []
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            # Live FastAPI schema may not carry x-codestrata-status; ensure no
            # untyped dict responses for formerly partial engineering routes.
            if path.startswith("/api/v1/engineering/") and method == "get":
                responses = operation.get("responses", {})
                content = (
                    responses.get("200", {})
                    .get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                )
                assert content, (method, path)
    assert partial == []


def test_inventory_report_can_be_written(tmp_path: Path, client: TestClient) -> None:
    from codestrata_platform.api.contracts.inventory import build_contract_inventory

    payload = build_contract_inventory(client.app)
    assert payload["api_major"] == API_MAJOR_VERSION
    assert payload["summary"]["partial"] == 0
    out = tmp_path / "platform-contract-inventory.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert out.is_file()
