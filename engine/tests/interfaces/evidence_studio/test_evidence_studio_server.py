from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from urllib.request import Request, urlopen

from codestrata.interfaces.evidence_studio import EvidenceStudioServer
from codestrata.interfaces.evidence_studio.repository_acquisition import (
    AcquiredRepository,
)


class _FixtureAcquirer:
    def __init__(self, repository: Path) -> None:
        self.repository = repository

    def acquire(self, url: str, requested_ref: str | None = None) -> AcquiredRepository:
        assert url == "https://github.com/example/fixture"
        assert requested_ref == "main"
        return AcquiredRepository(
            path=self.repository,
            source_url=url,
            display_name="example/fixture",
            revision="b" * 40,
            requested_ref=requested_ref,
            cached=False,
        )


def _request(url: str, *, payload: dict[str, object] | None = None) -> dict[str, object]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST" if body is not None else "GET",
    )
    with urlopen(request, timeout=5) as response:  # noqa: S310 - loopback test server
        return json.loads(response.read())


def test_loopback_api_bootstrap_preview_and_run(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "main.py").write_text("print('hello')\n", encoding="utf-8")
    server = EvidenceStudioServer(
        repository=repository,
        port=0,
        output_root=tmp_path / "artifacts",
    )
    server.start()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = server.url.removesuffix(f"/?token={server.token}")
    try:
        bootstrap = _request(f"{base}/api/bootstrap?token={server.token}")
        assert bootstrap["repository"] == str(repository)
        assert bootstrap["plan_schema"]
        catalog = bootstrap["catalog"]
        assert isinstance(catalog, dict)
        assert catalog["detected_languages"] == ["python"]
        assert any(item["collector_id"] == "language.python.core" for item in catalog["collectors"])
        plan = bootstrap["plan"]
        assert isinstance(plan, dict)
        plan = _request(
            f"{base}/api/plan/packs?token={server.token}",
            payload={
                "plan": plan,
                "packs": [
                    "repository-baseline@1.0",
                    "language-intelligence@1.0",
                ],
            },
        )
        assert any(item["collector_id"] == "language.python.core" for item in plan["activities"])
        preview = _request(f"{base}/api/preview?token={server.token}", payload=plan)
        assert preview["leaves_machine"] == ["Nothing; every selected activity is local-only."]
        job = _request(f"{base}/api/runs?token={server.token}", payload=plan)
        for _ in range(100):
            job = _request(f"{base}/api/runs/{job['job_id']}?token={server.token}")
            if job["status"] in {"completed", "partial", "failed", "cancelled"}:
                break
            time.sleep(0.02)
        assert job["status"] == "completed"
        result = job["result"]
        assert isinstance(result, dict)
        assert Path(str(result["report_path"])).is_file()
        assert job["events"]
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_loopback_api_acquires_github_repository_and_rebuilds_plan(
    tmp_path: Path,
) -> None:
    initial = tmp_path / "initial"
    initial.mkdir()
    remote = tmp_path / "github" / "fixture"
    remote.mkdir(parents=True)
    (remote / "package.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
    server = EvidenceStudioServer(
        repository=initial,
        port=0,
        output_root=tmp_path / "artifacts",
        repository_acquirer=_FixtureAcquirer(remote),
    )
    server.start()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = server.url.removesuffix(f"/?token={server.token}")
    try:
        acquired = _request(
            f"{base}/api/repositories/github?token={server.token}",
            payload={
                "url": "https://github.com/example/fixture",
                "ref": "main",
            },
        )
        assert acquired["repository"] == str(remote)
        assert acquired["repository_source"] == {
            "kind": "github",
            "display_name": "example/fixture",
            "path": str(remote),
            "source_url": "https://github.com/example/fixture",
            "requested_ref": "main",
            "revision": "b" * 40,
            "cached": False,
        }
        plan = acquired["plan"]
        assert isinstance(plan, dict)
        assert plan["subject"]["path"] == str(remote)
        assert plan["subject"]["repository_id"] == "fixture"
        assert acquired["preview"]
    finally:
        server.shutdown()
        thread.join(timeout=2)
