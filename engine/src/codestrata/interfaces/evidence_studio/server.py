"""Dependency-free localhost server for the Evidence Studio web application."""

from __future__ import annotations

import json
import secrets
import threading
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.parse import parse_qs, urlparse

import yaml
from pydantic import ValidationError

from codestrata.application.evidence.framework.service import (
    EvidenceFrameworkService,
    EvidenceRunResult,
)
from codestrata.domain.evidence.framework.models import EvidencePlan, ExecutionEvent
from codestrata.interfaces.evidence_studio.repository_acquisition import (
    AcquiredRepository,
    GitHubRepositoryAcquirer,
)
from codestrata.security.redaction import redact_report_value, redact_secrets

_MAX_REQUEST_BYTES = 2_000_000


class RepositoryAcquirer(Protocol):
    def acquire(self, url: str, requested_ref: str | None = None) -> AcquiredRepository: ...


@dataclass
class _RunJob:
    job_id: str
    status: str = "queued"
    events: list[ExecutionEvent] = field(default_factory=list)
    cancel: threading.Event = field(default_factory=threading.Event)
    result: EvidenceRunResult | None = None
    error: str | None = None

    def payload(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "events": [item.model_dump(mode="json") for item in self.events],
            "error": self.error,
            "result": (
                {
                    "run": self.result.run.model_dump(mode="json"),
                    "assessment": self.result.assessment.model_dump(mode="json"),
                    "evidence_count": len(self.result.evidence),
                    "output_directory": str(self.result.output_directory),
                    "report_path": str(self.result.output_directory / "report.html"),
                }
                if self.result
                else None
            ),
        }


class EvidenceStudioServer:
    """Serve one repository workflow on loopback with a per-process CSRF token."""

    def __init__(
        self,
        *,
        repository: Path,
        host: str = "127.0.0.1",
        port: int = 8765,
        output_root: Path | None = None,
        service: EvidenceFrameworkService | None = None,
        repository_acquirer: RepositoryAcquirer | None = None,
    ) -> None:
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("Evidence Studio must bind to a loopback address")
        self.repository = repository.expanduser().resolve()
        self.host = host
        self.port = port
        self._output_root_override = output_root.resolve() if output_root else None
        self.output_root = (
            self._output_root_override or self.repository / ".codestrata-artifacts"
        ).resolve()
        self.service = service or EvidenceFrameworkService()
        self.repository_acquirer = repository_acquirer or GitHubRepositoryAcquirer()
        self.repository_source: dict[str, Any] = {
            "kind": "local",
            "display_name": self.repository.name or str(self.repository),
            "path": str(self.repository),
            "source_url": None,
            "requested_ref": None,
            "revision": None,
            "cached": False,
        }
        self.token = secrets.token_urlsafe(24)
        self.jobs: dict[str, _RunJob] = {}
        self._jobs_lock = threading.Lock()
        self._repository_lock = threading.Lock()
        self._httpd: ThreadingHTTPServer | None = None

    @property
    def url(self) -> str:
        actual_port = self._httpd.server_port if self._httpd else self.port
        return f"http://127.0.0.1:{actual_port}/?token={self.token}"

    def start(self) -> None:
        handler = self._handler_type()
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)

    def serve_forever(self) -> None:
        if self._httpd is None:
            self.start()
        assert self._httpd is not None
        self._httpd.serve_forever()

    def shutdown(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()

    def _start_job(self, plan: EvidencePlan) -> _RunJob:
        job = _RunJob(job_id=str(uuid.uuid4()))
        with self._jobs_lock:
            self.jobs[job.job_id] = job

        def execute() -> None:
            job.status = "running"

            def capture(event: ExecutionEvent) -> None:
                with self._jobs_lock:
                    job.events.append(event)

            try:
                result = self.service.run(
                    plan,
                    output_root=self.output_root,
                    on_event=capture,
                    cancel=job.cancel,
                )
                job.result = result
                job.status = result.run.status.value
            except Exception as error:  # noqa: BLE001 - convert to local API state
                job.error = redact_secrets(str(error))
                job.status = "failed"

        threading.Thread(target=execute, daemon=True, name=f"evidence-{job.job_id}").start()
        return job

    def _bootstrap_payload(self) -> dict[str, Any]:
        plan = self.service.create_default_plan(self.repository)
        catalog = self.service.catalog(self.repository)
        source = dict(self.repository_source)
        if not source.get("revision"):
            source["revision"] = plan.subject.revision
        collector_status: dict[str, dict[str, Any]] = {}
        for item in self.service.registry.manifests():
            available, reason = self.service.registry.get(item.collector_id).available()
            collector_status[item.collector_id] = {
                "available": available,
                "reason": reason,
            }
        return {
            "plan": plan.model_dump(mode="json"),
            "plan_schema": EvidencePlan.model_json_schema(),
            "collectors": [
                item.model_dump(mode="json") for item in self.service.registry.manifests()
            ],
            "catalog": catalog.model_dump(mode="json"),
            "collector_status": collector_status,
            "profiles": [
                item.model_dump(mode="json") for item in self.service.profile_registry.manifests()
            ],
            "preview": self.service.preview(plan).model_dump(mode="json"),
            "repository": str(self.repository),
            "repository_source": source,
            "output_root": str(self.output_root),
        }

    def _acquire_github_repository(self, url: str, requested_ref: str | None) -> dict[str, Any]:
        with self._repository_lock:
            with self._jobs_lock:
                if any(job.status in {"queued", "running"} for job in self.jobs.values()):
                    raise ValueError(
                        "Wait for the current evidence run to finish before changing repositories."
                    )
            acquired: AcquiredRepository = self.repository_acquirer.acquire(url, requested_ref)
            self.repository = acquired.path.resolve()
            self.output_root = (
                self._output_root_override or self.repository / ".codestrata-artifacts"
            ).resolve()
            self.repository_source = {
                "kind": "github",
                "display_name": acquired.display_name,
                "path": str(acquired.path),
                "source_url": acquired.source_url,
                "requested_ref": acquired.requested_ref,
                "revision": acquired.revision,
                "cached": acquired.cached,
            }
            return self._bootstrap_payload()

    def _handler_type(self) -> type[BaseHTTPRequestHandler]:
        studio = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "CodeStrataEvidenceStudio/1.0"

            def log_message(self, format: str, *args: object) -> None:
                return

            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path.startswith("/api/"):
                    if not self._authorized(parsed.query):
                        self._json(HTTPStatus.FORBIDDEN, {"error": "invalid studio token"})
                        return
                    self._api_get(parsed.path)
                    return
                self._static(parsed.path)

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if not self._authorized(parsed.query):
                    self._json(HTTPStatus.FORBIDDEN, {"error": "invalid studio token"})
                    return
                try:
                    self._api_post(parsed.path)
                except ValidationError as error:
                    self._json(
                        HTTPStatus.UNPROCESSABLE_ENTITY,
                        {
                            "error": "invalid evidence plan",
                            "details": redact_report_value(error.errors()),
                        },
                    )
                except (ValueError, OSError, json.JSONDecodeError, yaml.YAMLError) as error:
                    self._json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": redact_secrets(str(error))},
                    )

            def _authorized(self, query: str) -> bool:
                query_token = parse_qs(query).get("token", [""])[0]
                header_token = self.headers.get("X-CodeStrata-Studio-Token", "")
                return secrets.compare_digest(query_token or header_token, studio.token)

            def _api_get(self, path: str) -> None:
                if path == "/api/bootstrap":
                    self._json(HTTPStatus.OK, studio._bootstrap_payload())
                    return
                if path.startswith("/api/runs/") and path.endswith("/report"):
                    job_id = path.removeprefix("/api/runs/").removesuffix("/report")
                    with studio._jobs_lock:
                        report_job = studio.jobs.get(job_id)
                    if report_job is None or report_job.result is None:
                        self._json(HTTPStatus.NOT_FOUND, {"error": "report not ready"})
                        return
                    report = report_job.result.output_directory / "report.html"
                    self._response(
                        HTTPStatus.OK,
                        report.read_bytes(),
                        "text/html; charset=utf-8",
                    )
                    return
                if path.startswith("/api/runs/"):
                    job_id = path.removeprefix("/api/runs/")
                    with studio._jobs_lock:
                        lookup_job = studio.jobs.get(job_id)
                    if lookup_job is None:
                        self._json(HTTPStatus.NOT_FOUND, {"error": "run job not found"})
                        return
                    self._json(HTTPStatus.OK, lookup_job.payload())
                    return
                self._json(HTTPStatus.NOT_FOUND, {"error": "API route not found"})

            def _api_post(self, path: str) -> None:
                if path == "/api/repositories/github":
                    payload = self._json_body()
                    url = payload.get("url")
                    requested_ref = payload.get("ref")
                    if not isinstance(url, str):
                        raise ValueError("GitHub repository URL is required.")
                    if requested_ref is not None and not isinstance(requested_ref, str):
                        raise ValueError("Branch or tag must be text.")
                    self._json(
                        HTTPStatus.OK,
                        studio._acquire_github_repository(url, requested_ref),
                    )
                    return
                if path == "/api/preview":
                    plan = EvidencePlan.model_validate(self._json_body())
                    self._json(
                        HTTPStatus.OK,
                        studio.service.preview(plan).model_dump(mode="json"),
                    )
                    return
                if path == "/api/plan/packs":
                    payload = self._json_body()
                    raw_plan = payload.get("plan")
                    raw_packs = payload.get("packs")
                    if not isinstance(raw_plan, dict):
                        raise ValueError("plan must be an object")
                    if not isinstance(raw_packs, list):
                        raise ValueError("packs must be an array")
                    plan = EvidencePlan.model_validate(raw_plan)
                    expanded = studio.service.apply_packs(
                        plan, tuple(str(item) for item in raw_packs)
                    )
                    self._json(HTTPStatus.OK, expanded.model_dump(mode="json"))
                    return
                if path == "/api/runs":
                    plan = EvidencePlan.model_validate(self._json_body())
                    job = studio._start_job(plan)
                    self._json(HTTPStatus.ACCEPTED, job.payload())
                    return
                if path.startswith("/api/runs/") and path.endswith("/cancel"):
                    job_id = path.removeprefix("/api/runs/").removesuffix("/cancel")
                    with studio._jobs_lock:
                        cancel_job = studio.jobs.get(job_id)
                    if cancel_job is None:
                        self._json(HTTPStatus.NOT_FOUND, {"error": "run job not found"})
                        return
                    cancel_job.cancel.set()
                    self._json(HTTPStatus.ACCEPTED, cancel_job.payload())
                    return
                if path == "/api/plan/yaml":
                    plan = EvidencePlan.model_validate(self._json_body())
                    content = yaml.safe_dump(
                        plan.model_dump(mode="json"),
                        allow_unicode=True,
                        sort_keys=True,
                    )
                    self._response(
                        HTTPStatus.OK,
                        content.encode("utf-8"),
                        "application/yaml; charset=utf-8",
                    )
                    return
                if path == "/api/plan/parse":
                    payload = yaml.safe_load(self._body().decode("utf-8"))
                    plan = EvidencePlan.model_validate(payload)
                    self._json(HTTPStatus.OK, plan.model_dump(mode="json"))
                    return
                self._json(HTTPStatus.NOT_FOUND, {"error": "API route not found"})

            def _body(self) -> bytes:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError as error:
                    raise ValueError("invalid content length") from error
                if length <= 0 or length > _MAX_REQUEST_BYTES:
                    raise ValueError("request body must be between 1 byte and 2 MB")
                return self.rfile.read(length)

            def _json_body(self) -> dict[str, Any]:
                payload = json.loads(self._body())
                if not isinstance(payload, dict):
                    raise ValueError("JSON request body must be an object")
                return cast(dict[str, Any], payload)

            def _static(self, path: str) -> None:
                assets = Path(__file__).with_name("assets")
                requested = "index.html" if path in {"", "/"} else path.lstrip("/")
                candidate = (assets / requested).resolve()
                if assets.resolve() not in candidate.parents and candidate != assets.resolve():
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                if not candidate.is_file():
                    candidate = assets / "index.html"
                if not candidate.is_file():
                    self._response(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        b"Evidence Studio assets have not been built.",
                        "text/plain; charset=utf-8",
                    )
                    return
                content_type = {
                    ".html": "text/html; charset=utf-8",
                    ".js": "text/javascript; charset=utf-8",
                    ".css": "text/css; charset=utf-8",
                    ".svg": "image/svg+xml",
                }.get(candidate.suffix, "application/octet-stream")
                self._response(HTTPStatus.OK, candidate.read_bytes(), content_type)

            def _json(self, status: HTTPStatus, payload: Any) -> None:
                self._response(
                    status,
                    json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    "application/json; charset=utf-8",
                )

            def _response(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header(
                    "Content-Security-Policy",
                    "default-src 'self'; script-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'",
                )
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                self.wfile.write(body)

        return Handler
