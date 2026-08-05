"""Production foundation unwired checks for completion verification (Slice 8.15)."""

from __future__ import annotations

from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
    create_community_data_lake_store,
)
from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.errors import ERROR_AUTHENTICATION_UNAVAILABLE
from fastapi.testclient import TestClient

from verification.community_data_lake.inputs import project_stream_storage_object
from verification.community_data_lake_completion.models import CheckResult

REPO = Path(__file__).resolve().parents[3]
WIRING_PY = (
    REPO
    / "platform"
    / "src"
    / "codestrata_platform"
    / "community_cloud_api"
    / "deployment"
    / "wiring.py"
)
APP_PY = (
    REPO / "platform" / "src" / "codestrata_platform" / "community_cloud_api" / "app.py"
)

_INGESTION_ROUTES: tuple[tuple[str, str], ...] = (
    ("POST", "/api/v1/telemetry"),
    ("POST", "/api/v1/assessment-metadata"),
    ("POST", "/api/v1/cli-events"),
    ("POST", "/api/v1/extension-events"),
    ("POST", "/api/v1/ai-usage"),
)


def check_production() -> list[CheckResult]:
    settings = load_deployment_settings({})
    app = create_production_foundation_app(settings=settings)
    client = TestClient(app)
    wiring_text = WIRING_PY.read_text(encoding="utf-8")
    app_text = APP_PY.read_text(encoding="utf-8")
    registry = app.state.community_cloud_route_registry

    checks: list[CheckResult] = [
        CheckResult(
            name="production:health_ok",
            ok=client.get("/api/v1/health").status_code == 200,
            detail="200",
            category="production",
        ),
        CheckResult(
            name="production:six_routes",
            ok=registry.diagnostics().registered_route_count == 6,
            detail=f"count={registry.diagnostics().registered_route_count}",
            category="production",
        ),
        CheckResult(
            name="production:wiring_no_data_lake",
            ok="data_lake" not in wiring_text
            and "storage_factory" not in wiring_text
            and "create_community_data_lake_store" not in wiring_text,
            detail="unwired",
            category="production",
        ),
        CheckResult(
            name="production:app_no_storage_factory",
            ok="storage_factory" not in app_text
            and "create_community_data_lake_store" not in app_text,
            detail="unwired",
            category="production",
        ),
    ]

    bodies = _minimal_ingestion_bodies()
    for method, path in _INGESTION_ROUTES:
        route_key = path.rsplit("/", maxsplit=1)[-1].replace("-", "_")
        response = client.request(method, path, json=bodies[path])
        payload = response.json()
        checks.append(
            CheckResult(
                name=f"production:ingestion_503:{route_key}",
                ok=response.status_code == 503
                and payload.get("error", {}).get("code") == ERROR_AUTHENTICATION_UNAVAILABLE,
                detail=f"status={response.status_code}",
                category="production",
            )
        )

    store = create_community_data_lake_store()
    result = store.put_immutable_storage_object(project_stream_storage_object("telemetry"))
    checks.append(
        CheckResult(
            name="production:unavailable_factory_never_stored",
            ok=result.status != StorageWriteStatus.STORED,
            detail=result.status.value,
            category="production",
        )
    )
    return checks


def _minimal_ingestion_bodies() -> dict[str, dict[str, str]]:
    return {
        "/api/v1/telemetry": {
            "schema_version": "1.0",
            "event_id": "evt-test000000000000000000000001",
            "client_type": "codestrata_cli",
            "telemetry_type": "assessment_started",
        },
        "/api/v1/assessment-metadata": {
            "schema_version": "1.0",
            "event_id": "evt-test000000000000000000000002",
            "client_type": "codestrata_cli",
            "assessment_id": "asmt-test00000000000000000001",
            "repository_fingerprint": "repo-fp-test0000000001",
            "assessment_schema_version": "1.2",
        },
        "/api/v1/cli-events": {
            "schema_version": "1.0",
            "event_id": "evt-test000000000000000000000003",
            "client_type": "codestrata_cli",
            "operation": "assess",
            "lifecycle": "completed",
            "result": "success",
        },
        "/api/v1/extension-events": {
            "schema_version": "1.0",
            "event_id": "evt-test000000000000000000000004",
            "client_type": "vscode_extension",
            "operation": "assess",
            "lifecycle": "completed",
            "result": "success",
        },
        "/api/v1/ai-usage": {
            "schema_version": "1.0",
            "event_id": "evt-test000000000000000000000005",
            "client_type": "codestrata_cli",
            "capability": "assessment_advisor",
            "provider_family": "openai_compatible",
            "model_family": "gpt",
            "operation": "assess",
            "lifecycle": "completed",
            "result": "success",
        },
    }


__all__ = ["check_production"]
