"""Contract tests: live Platform routes must match canonical OpenAPI."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

OPENAPI_ROOT = Path(__file__).resolve().parents[2] / "api" / "openapi"
CANONICAL_JSON = OPENAPI_ROOT / "openapi.json"
CANONICAL_YAML = OPENAPI_ROOT / "openapi.yaml"

PARTIAL_MARKERS: set[tuple[str, str]] = set()



def _live_operations(client: TestClient) -> set[tuple[str, str]]:
    spec = client.get("/openapi.json").json()
    rows: set[tuple[str, str]] = set()
    for path, methods in spec["paths"].items():
        for method in methods:
            if method in {"get", "post", "put", "patch", "delete"}:
                rows.add((method, path))
    return rows


def _canonical_operations() -> dict[tuple[str, str], str]:
    assert CANONICAL_JSON.is_file(), "Run generate_openapi.py first"
    spec = json.loads(CANONICAL_JSON.read_text(encoding="utf-8"))
    rows: dict[tuple[str, str], str] = {}
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            rows[(method, path)] = str(operation.get("x-codestrata-status", ""))
    return rows


def test_canonical_openapi_files_exist() -> None:
    assert CANONICAL_JSON.is_file()
    assert CANONICAL_YAML.is_file()
    yaml_doc = yaml.safe_load(CANONICAL_YAML.read_text(encoding="utf-8"))
    assert yaml_doc["openapi"].startswith("3.1")
    assert yaml_doc["info"]["x-codestrata-audience"] == "internal"


def test_live_routes_match_canonical_openapi(client: TestClient) -> None:
    live = _live_operations(client)
    canonical = set(_canonical_operations())
    missing_from_canonical = live - canonical
    extra_in_canonical = canonical - live
    assert missing_from_canonical == set(), missing_from_canonical
    assert extra_in_canonical == set(), extra_in_canonical


def test_maturity_extensions_present() -> None:
    ops = _canonical_operations()
    assert ops
    for key, status in ops.items():
        assert status in {
            "implemented",
            "partial",
            "proposed",
            "deprecated",
            "internal",
        }, key
    for marker in PARTIAL_MARKERS:
        assert ops[marker] == "partial"


def test_no_unknown_status_values() -> None:
    spec = json.loads(CANONICAL_JSON.read_text(encoding="utf-8"))
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            assert "x-codestrata-status" in operation
            assert "x-codestrata-owner" in operation
            assert operation["x-codestrata-audience"] == "internal"
            assert operation.get("operationId")


def test_servers_and_security_documented() -> None:
    spec = json.loads(CANONICAL_JSON.read_text(encoding="utf-8"))
    urls = {server["url"] for server in spec["servers"]}
    assert "https://platform.codestrata.ai" in urls
    assert "http://127.0.0.1:8000" in urls
    assert "PlatformApiKey" in spec["components"]["securitySchemes"]
    assert spec["components"]["securitySchemes"]["PlatformJwt"][
        "x-codestrata-status"
    ] == "proposed"


def test_internal_docs_routes_served(client: TestClient) -> None:
    docs = client.get("/api/docs")
    assert docs.status_code == 200
    assert b"noindex" in docs.content
    assert b"Platform API" in docs.content

    yaml_resp = client.get("/api/openapi.yaml")
    assert yaml_resp.status_code == 200
    assert b"openapi:" in yaml_resp.content

    json_resp = client.get("/api/openapi.json")
    assert json_resp.status_code == 200
    body = json_resp.json()
    assert body["openapi"].startswith("3.1")

    token_css = client.get("/api/docs/static/design-tokens/tokens.css")
    assert token_css.status_code == 200
    assert b"--font-display" in token_css.content


def test_community_report_schema_not_duplicated() -> None:
    """Platform OpenAPI must reference Community report contract, not copy it."""

    text = CANONICAL_JSON.read_text(encoding="utf-8")
    # Pointer present
    assert "AssessmentReport.json" in text or "assessment/codestrata.io" in text
    # Must not embed full Community report schema as a Platform component dump
    assert "codestrata.io/v1.2/AssessmentReport" not in json.dumps(
        json.loads(text).get("components", {}).get("schemas", {})
    )
