"""RestPlatformClient against a live Platform ingestion API."""

from __future__ import annotations

import socket
import time
from threading import Thread

import uvicorn

from codestrata.integration.commercial.client import RestPlatformClient
from codestrata.integration.commercial.models import (
    CompleteAssessmentRequest,
    RegisterAssessmentRequest,
    RegisterRepositoryRequest,
)
from codestrata_platform.api import create_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_rest_platform_client_end_to_end() -> None:
    app = create_app(use_memory=True)
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.time() + 5
    while not server.started and time.time() < deadline:
        time.sleep(0.05)
    assert server.started

    try:
        # Seed org/workspace via Rest client base using urllib through temporary client helpers.
        import json
        import urllib.request

        def _post(path: str, payload: dict) -> dict:
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                return json.loads(response.read().decode("utf-8"))

        org = _post("/api/v1/organizations", {"name": "Acme"})
        workspace = _post(
            "/api/v1/workspaces",
            {"organization_id": org["id"], "name": "Engineering"},
        )

        client = RestPlatformClient(
            base_url=f"http://127.0.0.1:{port}",
            timeout_seconds=5.0,
            max_retries=1,
        )
        repo = client.register_repository(
            RegisterRepositoryRequest(
                organization_id=org["id"],
                workspace_id=workspace["id"],
                display_name="App",
                repository_url="https://github.com/acme/app",
                provider="github",
            )
        )
        assert repo.created is True
        looked = client.lookup_repository(
            workspace_id=workspace["id"],
            repository_url="https://github.com/acme/app",
        )
        assert looked is not None
        assert looked.repository_id == repo.repository_id

        assessment = client.register_assessment(
            RegisterAssessmentRequest(
                repository_id=repo.repository_id,
                workspace_id=workspace["id"],
                engine_assessment_id="engine-assessment:rest-1",
                engine_version="0.1.0",
                assessment_version="1.2.0",
            )
        )
        started = client.start_assessment(assessment.assessment_id)
        assert started.status == "running"
        completed = client.complete_assessment(
            CompleteAssessmentRequest(assessment_id=assessment.assessment_id)
        )
        assert completed.status == "succeeded"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
