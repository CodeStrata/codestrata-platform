"""Epic 8 false-acceptance prevention tests (Slice 8.15)."""

from __future__ import annotations

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


def test_unavailable_factory_never_stored() -> None:
    store = create_community_data_lake_store()
    result = store.put_immutable_storage_object(project_stream_storage_object("telemetry"))
    assert result.status != StorageWriteStatus.STORED


def test_production_ingest_returns_503_authentication_unavailable() -> None:
    client = TestClient(
        create_production_foundation_app(settings=load_deployment_settings({}))
    )
    response = client.post(
        "/api/v1/telemetry",
        json={
            "schema_version": "1.0",
            "event_id": "evt-test000000000000000000000001",
            "client_type": "codestrata_cli",
            "telemetry_type": "assessment_started",
        },
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE
