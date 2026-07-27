"""Ingestion API tests for assessment artifacts."""

from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient


def _checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _seed_assessment(client: TestClient) -> str:
    org = client.post("/api/v1/organizations", json={"name": "Acme"}).json()
    workspace = client.post(
        "/api/v1/workspaces",
        json={"organization_id": org["id"], "name": "Default"},
    ).json()
    repo = client.post(
        "/api/v1/repositories",
        json={
            "workspace_id": workspace["id"],
            "organization_id": org["id"],
            "display_name": "App",
            "provider": "github",
            "repository_url": "https://github.com/acme/app",
            "default_branch": "main",
            "visibility": "private",
        },
    ).json()
    assessment = client.post(
        "/api/v1/assessments",
        json={
            "repository_id": repo["id"],
            "workspace_id": workspace["id"],
            "engine_version": "1.0.0",
            "assessment_version": "0.1.0",
        },
    ).json()
    return assessment["id"]


def test_artifact_register_upload_complete_and_idempotent(client: TestClient) -> None:
    assessment_id = _seed_assessment(client)
    content = b'{"summary":true}'
    checksum = _checksum(content)
    register = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts",
        json={
            "engine_assessment_id": "engine-assessment:1",
            "artifact_type": "assessment_summary",
            "format": "json",
            "schema_version": "1.0",
            "checksum": checksum,
            "size_bytes": len(content),
            "metadata": {"kind": "summary"},
        },
    )
    assert register.status_code == 201
    body = register.json()
    artifact_id = body["artifact_id"]

    duplicate = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts",
        json={
            "engine_assessment_id": "engine-assessment:1",
            "artifact_type": "assessment_summary",
            "format": "json",
            "schema_version": "1.0",
            "checksum": checksum,
            "size_bytes": len(content),
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["artifact_id"] == artifact_id
    assert duplicate.json()["created"] is False

    upload = client.put(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}",
        content=content,
        headers={
            "Content-Type": "application/json",
            "X-CodeStrata-Checksum": checksum,
        },
    )
    assert upload.status_code == 200
    assert upload.json()["status"] == "uploading"
    assert "storage_key" in upload.json()
    assert "/" not in (upload.json().get("storage_key") or "").split("..")

    complete = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}/complete"
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"
    assert complete.json().get("storage_path") is None

    listed = client.get(f"/api/v1/ingestion/assessments/{assessment_id}/artifacts")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    details = client.get(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}"
    )
    assert details.status_code == 200
    assert details.json()["checksum"] == checksum


def test_artifact_checksum_mismatch_and_not_found(client: TestClient) -> None:
    assessment_id = _seed_assessment(client)
    content = b'{"ok":true}'
    checksum = _checksum(content)
    registered = client.post(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts",
        json={
            "engine_assessment_id": "engine-assessment:2",
            "artifact_type": "report_json",
            "format": "json",
            "schema_version": "1.0",
            "checksum": checksum,
            "size_bytes": len(content),
        },
    ).json()
    mismatch = client.put(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{registered['artifact_id']}",
        content=content,
        headers={
            "Content-Type": "application/json",
            "X-CodeStrata-Checksum": _checksum(b"other"),
        },
    )
    assert mismatch.status_code == 422

    missing = client.get(
        f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/artifact:missing"
    )
    assert missing.status_code == 404


def test_durable_artifact_content_survives_restart(api_postgres_url: str, tmp_path) -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from codestrata_platform.api import create_app
    from codestrata_platform.infrastructure.persistence import (
        create_engine_from_url,
        create_platform_schema,
    )

    engine = create_engine_from_url(api_postgres_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    create_platform_schema(engine)
    engine.dispose()

    artifact_root = tmp_path / "artifacts"
    content = b'{"persist":true}'
    checksum = _checksum(content)

    app1 = create_app(
        database_url=api_postgres_url,
        artifact_storage_root=artifact_root,
    )
    with TestClient(app1) as client:
        assessment_id = _seed_assessment(client)
        registered = client.post(
            f"/api/v1/ingestion/assessments/{assessment_id}/artifacts",
            json={
                "engine_assessment_id": "engine-assessment:persist",
                "artifact_type": "assessment_summary",
                "format": "json",
                "schema_version": "1.0",
                "checksum": checksum,
                "size_bytes": len(content),
            },
        ).json()
        artifact_id = registered["artifact_id"]
        upload = client.put(
            f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}",
            content=content,
            headers={
                "Content-Type": "application/json",
                "X-CodeStrata-Checksum": checksum,
            },
        )
        assert upload.status_code == 200
        complete = client.post(
            f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}/complete"
        )
        assert complete.status_code == 200

    app2 = create_app(
        database_url=api_postgres_url,
        artifact_storage_root=artifact_root,
    )
    with TestClient(app2) as client:
        details = client.get(
            f"/api/v1/ingestion/assessments/{assessment_id}/artifacts/{artifact_id}"
        )
        assert details.status_code == 200
        assert details.json()["status"] == "completed"
        assert details.json()["engine_assessment_id"] == "engine-assessment:persist"
        storage_key = details.json()["storage_key"]
        assert storage_key is not None
        assert (artifact_root / storage_key).is_file()
