"""Engine client for Community report publishing (Slice 17.16)."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from codestrata.community_cloud.public_api_authority import resolve_public_community_api_base
from codestrata.telemetry.event_identity import TelemetryTransportCredential
from codestrata.telemetry.session import TelemetrySession

PUBLIC_REPORTS_BASE_URL = "https://reports.codestrata.ai"
CREDENTIAL_ENV = "CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL"
PRIVATE_REPO_WARNING = (
    "Publishing creates a publicly accessible report. Anyone with the link can view it."
)


class ReportPublishError(RuntimeError):
    """Raised for explicit publish failures — never includes credentials."""


@dataclass(frozen=True, slots=True)
class ReportPublishResult:
    public_id: str
    public_url: str
    report_type: str
    status: str = "published"

    def to_stable_dict(self) -> dict[str, str]:
        return {
            "public_id": self.public_id,
            "public_url": self.public_url,
            "report_type": self.report_type,
            "status": self.status,
        }


def telemetry_eligible_for_publish(session: TelemetrySession | None) -> bool:
    if session is None:
        return False
    return bool(session.transmission_authorized)


def resolve_community_credential() -> TelemetryTransportCredential:
    raw = (os.environ.get(CREDENTIAL_ENV) or "").strip()
    if not raw:
        raise ReportPublishError(
            f"Missing {CREDENTIAL_ENV}. Cloud publishing requires Community client credentials."
        )
    return TelemetryTransportCredential(raw)


def _api_url(path: str) -> str:
    base = resolve_public_community_api_base().rstrip("/")
    return f"{base}{path}"


def _request_json(
    *,
    method: str,
    url: str,
    credential: TelemetryTransportCredential,
    body: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if body is None else json.dumps(body, sort_keys=True).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "Authorization": credential.authorization_header_value(),
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )
    try:
        with opener.open(request, timeout=30) as response:
            raw = response.read(1_000_000)
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        raw = exc.read(1_000_000)
        status = int(exc.code)
    except Exception as exc:  # noqa: BLE001
        raise ReportPublishError(f"publish API unavailable: {type(exc).__name__}") from exc
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except json.JSONDecodeError as exc:
        raise ReportPublishError("invalid publish API response") from exc
    if not isinstance(payload, dict):
        raise ReportPublishError("invalid publish API response")
    return status, payload


def _put_bytes(url: str, body: bytes, *, content_type: str) -> None:
    # Staging upload only — never treat as public report URL.
    host = (urlparse(url).hostname or "").lower()
    if host.endswith("codestrata.ai") and host.startswith("reports."):
        raise ReportPublishError("refusing to PUT to public reports host")

    class _PutRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
            if code not in {301, 302, 303, 307, 308}:
                return None
            # S3 may 307 from path-style to virtual-hosted endpoints on PUT.
            method = req.get_method()
            data = req.data
            headers_out = {
                k: v
                for k, v in req.headers.items()
                if k.lower() not in {"content-length", "content-type"}
                or method in {"GET", "HEAD"}
            }
            if method not in {"GET", "HEAD"} and req.headers.get("Content-type"):
                headers_out["Content-type"] = req.headers.get("Content-type")
            return urllib.request.Request(
                newurl,
                data=data,
                headers=headers_out,
                method=method,
                unverifiable=True,
            )

    request = urllib.request.Request(
        url,
        data=body,
        method="PUT",
        headers={"Content-Type": content_type},
    )
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        _PutRedirectHandler(),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
    )
    try:
        with opener.open(request, timeout=120) as response:
            _ = response.read(1024)
            status = int(getattr(response, "status", 200))
    except urllib.error.HTTPError as exc:
        raise ReportPublishError(f"artifact upload failed ({exc.code})") from exc
    except Exception as exc:  # noqa: BLE001
        raise ReportPublishError(f"artifact upload unavailable: {type(exc).__name__}") from exc
    if status >= 300:
        raise ReportPublishError(f"artifact upload failed ({status})")


def publish_local_assessment(
    *,
    current_dir: Path,
    logical_repository_id: str,
    session: TelemetrySession | None,
    private_repository_acknowledged: bool,
    confirm_public_publish: bool,
    credential: TelemetryTransportCredential | None = None,
) -> ReportPublishResult:
    """Upload local CURRENT assessment HTML+JSON and return branded public URL."""

    if not telemetry_eligible_for_publish(session):
        raise ReportPublishError(
            "Cloud publishing requires telemetry/cloud participation "
            "(telemetry opt-in). Local report remains available."
        )
    if not confirm_public_publish:
        raise ReportPublishError("Explicit publish confirmation is required.")
    if logical_repository_id.startswith("local-") and not private_repository_acknowledged:
        raise ReportPublishError(PRIVATE_REPO_WARNING)

    html_path = current_dir / "assessment.html"
    json_path = current_dir / "assessment.json"
    if not html_path.is_file() or not json_path.is_file():
        raise ReportPublishError("Local current assessment.html/json not found.")

    active_cred = credential or resolve_community_credential()
    status, intent = _request_json(
        method="POST",
        url=_api_url("/api/v1/reports/upload-intents"),
        credential=active_cred,
        body={
            "schema_version": "1.0",
            "report_type": "assessment",
            "logical_identity_type": "repository",
            "logical_identity_key": logical_repository_id,
            "artifacts": ["assessment.html", "assessment.json"],
            "private_repository_acknowledged": private_repository_acknowledged,
            "confirm_public_publish": True,
        },
    )
    if status >= 300:
        raise ReportPublishError(
            f"upload intent refused ({status}): {intent.get('error') or intent.get('code') or 'error'}"
        )
    upload_id = str(intent.get("upload_id") or "")
    puts = intent.get("puts") or []
    if not upload_id or not isinstance(puts, list):
        raise ReportPublishError("invalid upload intent response")

    local_files = {
        "assessment.html": html_path.read_bytes(),
        "assessment.json": json_path.read_bytes(),
    }
    for item in puts:
        if not isinstance(item, dict):
            continue
        name = str(item.get("artifact") or "")
        url = str(item.get("upload_url") or "")
        ctype = str(item.get("content_type") or "application/octet-stream")
        if name not in local_files or not url:
            raise ReportPublishError("incomplete upload intent")
        # Never return staging URL as public share link.
        if "s3.amazonaws.com" in url or "amazonaws.com" in url:
            pass  # expected for private staging PUT
        _put_bytes(url, local_files[name], content_type=ctype)

    status, published = _request_json(
        method="POST",
        url=_api_url("/api/v1/reports"),
        credential=active_cred,
        body={
            "schema_version": "1.0",
            "upload_id": upload_id,
            "confirm_public_publish": True,
            "private_repository_acknowledged": private_repository_acknowledged,
        },
    )
    if status >= 300:
        raise ReportPublishError(
            f"publish refused ({status}): {published.get('error') or published.get('code') or 'error'}"
        )
    public_url = str(published.get("public_url") or "")
    public_id = str(published.get("public_id") or "")
    if not public_url.startswith(PUBLIC_REPORTS_BASE_URL + "/r/"):
        raise ReportPublishError("publish response missing branded public URL")
    if "s3.amazonaws.com" in public_url or "amazonaws.com" in public_url:
        raise ReportPublishError("refusing raw S3 public URL")
    return ReportPublishResult(
        public_id=public_id,
        public_url=public_url,
        report_type="assessment",
    )


def publish_local_eir(
    *,
    current_dir: Path,
    portfolio_id: str,
    session: TelemetrySession | None,
    confirm_public_publish: bool,
    credential: TelemetryTransportCredential | None = None,
) -> ReportPublishResult:
    if not telemetry_eligible_for_publish(session):
        raise ReportPublishError(
            "Cloud publishing requires telemetry/cloud participation "
            "(telemetry opt-in). Local report remains available."
        )
    if not confirm_public_publish:
        raise ReportPublishError("Explicit publish confirmation is required.")

    html_path = current_dir / "engineering-intelligence-report.html"
    json_path = current_dir / "engineering-intelligence-report.json"
    if not html_path.is_file() or not json_path.is_file():
        raise ReportPublishError("Local current EIR html/json not found.")

    active_cred = credential or resolve_community_credential()
    status, intent = _request_json(
        method="POST",
        url=_api_url("/api/v1/reports/upload-intents"),
        credential=active_cred,
        body={
            "schema_version": "1.0",
            "report_type": "engineering_intelligence",
            "logical_identity_type": "portfolio",
            "logical_identity_key": portfolio_id,
            "artifacts": [
                "engineering-intelligence-report.html",
                "engineering-intelligence-report.json",
            ],
            "private_repository_acknowledged": True,
            "confirm_public_publish": True,
        },
    )
    if status >= 300:
        raise ReportPublishError(
            f"upload intent refused ({status}): {intent.get('error') or intent.get('code') or 'error'}"
        )
    upload_id = str(intent.get("upload_id") or "")
    puts = intent.get("puts") or []
    local_files = {
        "engineering-intelligence-report.html": html_path.read_bytes(),
        "engineering-intelligence-report.json": json_path.read_bytes(),
    }
    for item in puts:
        if not isinstance(item, dict):
            continue
        name = str(item.get("artifact") or "")
        url = str(item.get("upload_url") or "")
        ctype = str(item.get("content_type") or "application/octet-stream")
        _put_bytes(url, local_files[name], content_type=ctype)

    status, published = _request_json(
        method="POST",
        url=_api_url("/api/v1/reports"),
        credential=active_cred,
        body={
            "schema_version": "1.0",
            "upload_id": upload_id,
            "confirm_public_publish": True,
            "private_repository_acknowledged": True,
        },
    )
    if status >= 300:
        raise ReportPublishError(
            f"publish refused ({status}): {published.get('error') or published.get('code') or 'error'}"
        )
    public_url = str(published.get("public_url") or "")
    public_id = str(published.get("public_id") or "")
    if not public_url.startswith(PUBLIC_REPORTS_BASE_URL + "/r/"):
        raise ReportPublishError("publish response missing branded public URL")
    return ReportPublishResult(
        public_id=public_id,
        public_url=public_url,
        report_type="engineering_intelligence",
    )


__all__ = [
    "CREDENTIAL_ENV",
    "PRIVATE_REPO_WARNING",
    "PUBLIC_REPORTS_BASE_URL",
    "ReportPublishError",
    "ReportPublishResult",
    "publish_local_assessment",
    "publish_local_eir",
    "resolve_community_credential",
    "telemetry_eligible_for_publish",
]
