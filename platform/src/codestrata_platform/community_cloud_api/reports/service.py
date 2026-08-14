"""Report publishing service — upload intent, publish, public get, revoke."""

from __future__ import annotations

import time
from typing import Any, Callable

from starlette.responses import RedirectResponse, Response

from codestrata_platform.community_cloud_api.errors import (
    ERROR_ARTIFACT_MISSING,
    ERROR_ARTIFACT_TOO_LARGE,
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_EXPLICIT_PUBLISH_REQUIRED,
    ERROR_FORBIDDEN,
    ERROR_INVALID_REQUEST_SCHEMA,
    ERROR_NOT_FOUND,
    ERROR_PRIVATE_REPOSITORY_ACK_REQUIRED,
    ERROR_REPORT_NOT_FOUND,
    ERROR_REPORT_STORE_UNAVAILABLE,
    ERROR_SANITIZER_REJECTED,
    ERROR_UPLOAD_INTENT_EXPIRED,
)
from codestrata_platform.community_cloud_api.models import RequestContext
from codestrata_platform.community_cloud_api.reports.ids import (
    generate_public_report_id,
    generate_upload_id,
    validate_public_report_id,
)
from codestrata_platform.community_cloud_api.reports.feedback import (
    FEEDBACK_SUMMARY_KEY,
    ReportFeedbackRequest,
    apply_feedback_vote,
    empty_feedback_summary,
    feedback_vote_key,
)
from codestrata_platform.community_cloud_api.reports.feedback_chrome import (
    apply_published_feedback_csp,
    feedback_chrome_html,
)
from codestrata_platform.community_cloud_api.reports.models import (
    ReportPublishRequest,
    ReportUploadIntentRequest,
    public_safe_metadata,
    validate_artifact_set,
)
from codestrata_platform.community_cloud_api.reports.policy import (
    LOGICAL_PORTFOLIO,
    LOGICAL_REPOSITORY,
    MAX_ARTIFACT_BYTES,
    REPORT_TYPE_ASSESSMENT,
    REPORT_TYPE_EIR,
    SLOT_CURRENT,
    SLOT_PREVIOUS,
    STATUS_PUBLISHED,
    STATUS_REVOKED,
    UPLOAD_INTENT_TTL_SECONDS,
    CommunityReportPublishingPolicy,
    default_report_publishing_policy,
    public_report_url,
)
from codestrata_platform.community_cloud_api.reports.sanitizer import sanitize_report_bytes
from codestrata_platform.community_cloud_api.reports.store import (
    InMemoryReportArtifactStore,
    ReportArtifactStore,
)
from codestrata_platform.community_cloud_api.reports.validation_registry import (
    VALIDATION_ENTRIES_PREFIX,
    VERIFICATION_FAILED,
    VERIFICATION_PENDING,
    VERIFICATION_VERIFIED,
    build_validation_entry,
    sanitize_list_limit,
    validation_entry_key,
)
from codestrata_platform.community_cloud_api.serialization import (
    build_error_response,
    build_json_response,
)

Clock = Callable[[], float]


def _content_type_for(name: str) -> str:
    if name.endswith(".html"):
        return "text/html; charset=utf-8"
    if name.endswith(".json"):
        return "application/json"
    return "application/octet-stream"


def _artifact_prefix(report_type: str, logical_key: str, slot: str) -> str:
    if report_type == REPORT_TYPE_ASSESSMENT:
        return f"artifacts/assessments/{logical_key}/{slot}/"
    return f"artifacts/intelligence/{logical_key}/{slot}/"


def _logic_key(report_type: str, logical_key: str) -> str:
    return f"metadata/logic/{report_type}/{logical_key}.json"


def _public_meta_key(public_id: str) -> str:
    return f"metadata/public/{public_id}.json"


def _staging_prefix(upload_id: str) -> str:
    return f"staging/{upload_id}/"


def _chrome_html(
    *,
    inner_html: str,
    report_type: str,
    generated_at: str | None,
    engine_version: str | None,
    public_id: str,
) -> str:
    label = (
        "Assessment Report"
        if report_type == REPORT_TYPE_ASSESSMENT
        else "Engineering Intelligence Report"
    )
    meta_bits = [
        f'<meta name="codestrata-report-type" content="{report_type}">',
        f'<meta name="codestrata-public-id" content="{public_id}">',
    ]
    if generated_at:
        meta_bits.append(
            f'<meta name="codestrata-generated-at" content="{generated_at}">'
        )
    if engine_version:
        meta_bits.append(
            f'<meta name="codestrata-engine-version" content="{engine_version}">'
        )
    banner = (
        '<header style="font-family:system-ui,sans-serif;padding:12px 16px;'
        "border-bottom:1px solid #d0d7de;background:#f6f8fa;\">"
        "<strong>CodeStrata</strong> · "
        f"{label}"
        + (f" · generated {generated_at}" if generated_at else "")
        + (f" · engine {engine_version}" if engine_version else "")
        + '<div style="margin-top:6px;font-size:12px;color:#57606a;">'
        "Public share link. Anyone with this URL can view the report. "
        "Not stored in the Community Data Lake."
        "</div></header>"
    )
    feedback, script_nonce = feedback_chrome_html(public_id=public_id)
    # If the artifact is a full HTML document, inject banner after <body>
    # and feedback before </body>.
    lower = inner_html.lower()
    body_idx = lower.find("<body")
    if body_idx >= 0:
        gt = inner_html.find(">", body_idx)
        if gt >= 0:
            injected = (
                inner_html[: gt + 1]
                + "".join(meta_bits)
                + banner
                + inner_html[gt + 1 :]
            )
            close_idx = injected.lower().rfind("</body>")
            if close_idx >= 0:
                assembled = injected[:close_idx] + feedback + injected[close_idx:]
            else:
                assembled = injected + feedback
            return apply_published_feedback_csp(assembled, nonce=script_nonce)
    assembled = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        + "".join(meta_bits)
        + f"<title>CodeStrata {label}</title></head><body>"
        + banner
        + inner_html
        + feedback
        + "</body></html>"
    )
    return apply_published_feedback_csp(assembled, nonce=script_nonce)


def _owner_ref(principal: object) -> str:
    return (
        getattr(principal, "rate_limit_scope_id", None)
        or getattr(principal, "credential_id", None)
        or getattr(principal, "safe_client_reference", None)
        or "unknown"
    )


class ReportPublishingService:
    """Authenticated publish/revoke + public read for report artifacts."""

    def __init__(
        self,
        *,
        store: ReportArtifactStore | None = None,
        policy: CommunityReportPublishingPolicy | None = None,
        clock: Clock | None = None,
        available: bool = True,
    ) -> None:
        self._store = store if store is not None else InMemoryReportArtifactStore()
        self._policy = policy or default_report_publishing_policy()
        self._clock = clock or time.time
        self._available = available

    def handle_upload_intent(self, context: RequestContext) -> Response:
        if not self._available:
            return self._unavailable(context)
        principal = context.authenticated_client
        if principal is None:
            return build_error_response(
                ERROR_AUTHENTICATION_REQUIRED,
                http_status=401,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        req = context.validated_request
        if not isinstance(req, ReportUploadIntentRequest):
            return build_error_response(
                ERROR_INVALID_REQUEST_SCHEMA,
                http_status=422,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        if not req.confirm_public_publish:
            return build_error_response(
                ERROR_EXPLICIT_PUBLISH_REQUIRED,
                http_status=400,
                api_version=context.api_version,
                request_id=context.request_id,
                details={"message": "confirm_public_publish must be true"},
            )
        if (
            req.report_type == REPORT_TYPE_ASSESSMENT
            and req.logical_identity_type == LOGICAL_REPOSITORY
            and req.logical_identity_key.startswith("local-")
            and not req.private_repository_acknowledged
        ):
            return build_error_response(
                ERROR_PRIVATE_REPOSITORY_ACK_REQUIRED,
                http_status=400,
                api_version=context.api_version,
                request_id=context.request_id,
                details={
                    "message": (
                        "Publishing creates a publicly accessible report. "
                        "Anyone with the link can view it."
                    )
                },
            )
        if req.report_type == REPORT_TYPE_EIR and req.logical_identity_type != LOGICAL_PORTFOLIO:
            return build_error_response(
                ERROR_INVALID_REQUEST_SCHEMA,
                http_status=400,
                api_version=context.api_version,
                request_id=context.request_id,
                details={"message": "EIR requires portfolio logical identity"},
            )
        if (
            req.report_type == REPORT_TYPE_ASSESSMENT
            and req.logical_identity_type != LOGICAL_REPOSITORY
        ):
            return build_error_response(
                ERROR_INVALID_REQUEST_SCHEMA,
                http_status=400,
                api_version=context.api_version,
                request_id=context.request_id,
                details={"message": "assessment requires repository logical identity"},
            )
        try:
            validate_artifact_set(req.report_type, req.artifacts)
        except ValueError as exc:
            return build_error_response(
                ERROR_INVALID_REQUEST_SCHEMA,
                http_status=400,
                api_version=context.api_version,
                request_id=context.request_id,
                details={"message": str(exc)},
            )

        upload_id = generate_upload_id()
        now = float(self._clock())
        owner_ref = _owner_ref(principal)
        staging = _staging_prefix(upload_id)
        puts: list[dict[str, str]] = []
        for name in req.artifacts:
            key = f"{staging}{name}"
            ctype = _content_type_for(name)
            url = self._store.create_presigned_put(key, content_type=ctype)
            puts.append({"artifact": name, "content_type": ctype, "upload_url": url})

        intent = {
            "upload_id": upload_id,
            "owner_client_ref": owner_ref,
            "report_type": req.report_type,
            "logical_identity_type": req.logical_identity_type,
            "logical_identity_key": req.logical_identity_key,
            "artifacts": list(req.artifacts),
            "created_at": now,
            "expires_at": now + UPLOAD_INTENT_TTL_SECONDS,
            "private_repository_acknowledged": req.private_repository_acknowledged,
            "confirm_public_publish": True,
            "staging_prefix": staging,
        }
        self._store.put_json(f"{staging}intent.json", intent)

        return build_json_response(
            {
                "api_version": context.api_version,
                "upload_id": upload_id,
                "expires_in_seconds": UPLOAD_INTENT_TTL_SECONDS,
                "puts": puts,
                "max_artifact_bytes": MAX_ARTIFACT_BYTES,
                "note": (
                    "Upload URLs are temporary staging credentials. "
                    "They are not public report URLs."
                ),
            },
            status_code=201,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    def handle_publish(self, context: RequestContext) -> Response:
        if not self._available:
            return self._unavailable(context)
        principal = context.authenticated_client
        if principal is None:
            return build_error_response(
                ERROR_AUTHENTICATION_REQUIRED,
                http_status=401,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        req = context.validated_request
        if not isinstance(req, ReportPublishRequest):
            return build_error_response(
                ERROR_INVALID_REQUEST_SCHEMA,
                http_status=422,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        if not req.confirm_public_publish:
            return build_error_response(
                ERROR_EXPLICIT_PUBLISH_REQUIRED,
                http_status=400,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        staging = _staging_prefix(req.upload_id)
        intent = self._store.get_json(f"{staging}intent.json")
        if intent is None:
            return build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
                details={"message": "upload intent not found or expired"},
            )
        now = float(self._clock())
        if float(intent.get("expires_at") or 0) < now:
            self._store.delete_prefix(staging)
            return build_error_response(
                ERROR_UPLOAD_INTENT_EXPIRED,
                http_status=410,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        owner_ref = _owner_ref(principal)
        if intent.get("owner_client_ref") != owner_ref:
            return build_error_response(
                ERROR_FORBIDDEN,
                http_status=403,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        report_type = str(intent["report_type"])
        logical_key = str(intent["logical_identity_key"])
        artifacts = list(intent.get("artifacts") or [])
        loaded: dict[str, bytes] = {}
        for name in artifacts:
            body = self._store.get_bytes(f"{staging}{name}")
            if body is None:
                return build_error_response(
                    ERROR_ARTIFACT_MISSING,
                    http_status=400,
                    api_version=context.api_version,
                    request_id=context.request_id,
                    details={"artifact": name},
                )
            if len(body) > MAX_ARTIFACT_BYTES:
                return build_error_response(
                    ERROR_ARTIFACT_TOO_LARGE,
                    http_status=413,
                    api_version=context.api_version,
                    request_id=context.request_id,
                    details={"artifact": name},
                )
            check = sanitize_report_bytes(name=name, content=body)
            if not check.ok:
                return build_error_response(
                    ERROR_SANITIZER_REJECTED,
                    http_status=400,
                    api_version=context.api_version,
                    request_id=context.request_id,
                    details={"reason_code": check.reason_code},
                )
            loaded[name] = body

        if (
            report_type == REPORT_TYPE_ASSESSMENT
            and logical_key.startswith("local-")
            and not (
                intent.get("private_repository_acknowledged")
                or req.private_repository_acknowledged
            )
        ):
            return build_error_response(
                ERROR_PRIVATE_REPOSITORY_ACK_REQUIRED,
                http_status=400,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        public_id = generate_public_report_id()
        try:
            self._rotate_and_promote(
                report_type=report_type,
                logical_key=logical_key,
                artifacts=loaded,
                public_id=public_id,
                owner_ref=owner_ref,
            )
        except Exception:  # noqa: BLE001
            return build_error_response(
                ERROR_REPORT_STORE_UNAVAILABLE,
                http_status=503,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        self._store.delete_prefix(staging)
        url = public_report_url(public_id)
        return build_json_response(
            {
                "api_version": context.api_version,
                "public_id": public_id,
                "public_url": url,
                "report_type": report_type,
                "slot": SLOT_CURRENT,
                "status": STATUS_PUBLISHED,
                "retention": {
                    "max_versions": 2,
                    "note": "current+previous only; S3 versioning is ops recovery",
                },
            },
            status_code=201,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    def handle_public_get(self, context: RequestContext) -> Response:
        if not self._available:
            # Fail closed as not found for public callers (no store leakage).
            return build_error_response(
                ERROR_REPORT_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        public_id = (context.path_params or {}).get("public_id") or ""
        try:
            public_id = validate_public_report_id(public_id)
        except ValueError:
            return build_error_response(
                ERROR_REPORT_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        record = self._store.get_json(_public_meta_key(public_id))
        if record is None or record.get("status") != STATUS_PUBLISHED:
            return build_error_response(
                ERROR_REPORT_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        want_json = False
        format_hint = (context.path_params or {}).get("format") or ""
        if format_hint == "json":
            want_json = True

        prefix = str(record.get("artifact_prefix") or "")
        if want_json:
            json_name = (
                "assessment.json"
                if record.get("report_type") == REPORT_TYPE_ASSESSMENT
                else "engineering-intelligence-report.json"
            )
            body = self._store.get_bytes(f"{prefix}{json_name}")
            if body is None:
                return build_error_response(
                    ERROR_REPORT_NOT_FOUND,
                    http_status=404,
                    api_version=context.api_version,
                    request_id=context.request_id,
                )
            response = Response(
                content=body,
                status_code=200,
                media_type="application/json",
            )
        else:
            html_name = (
                "assessment.html"
                if record.get("report_type") == REPORT_TYPE_ASSESSMENT
                else "engineering-intelligence-report.html"
            )
            body = self._store.get_bytes(f"{prefix}{html_name}")
            if body is None:
                return build_error_response(
                    ERROR_REPORT_NOT_FOUND,
                    http_status=404,
                    api_version=context.api_version,
                    request_id=context.request_id,
                )
            # Lambda sync responses are capped near 6 MiB. Oversized HTML is
            # served via short-lived GetObject URL; the Worker follows it
            # server-side so the browser address bar stays on reports.codestrata.ai.
            max_inline = 5_000_000
            if len(body) > max_inline and hasattr(self._store, "create_presigned_get"):
                try:
                    signed = self._store.create_presigned_get(
                        f"{prefix}{html_name}",
                        expires_in=120,
                        response_content_type="text/html; charset=utf-8",
                    )
                except Exception:  # noqa: BLE001
                    signed = None
                if signed:
                    response = RedirectResponse(url=signed, status_code=307)
                    max_age = int(self._policy.cache_max_age_seconds)
                    response.headers["Cache-Control"] = (
                        f"private, max-age={max_age}, must-revalidate"
                    )
                    response.headers["X-Robots-Tag"] = "noindex"
                    response.headers["X-CodeStrata-Report-Delivery"] = "presigned_get"
                    if context.request_id:
                        response.headers["X-Request-Id"] = context.request_id
                    meta = public_safe_metadata(record)
                    response.headers["X-CodeStrata-Report-Type"] = str(
                        meta.get("report_type") or ""
                    )
                    # Stable identity for independent publish verification without
                    # downloading multi-MB HTML (chrome is skipped on this path).
                    response.headers["X-CodeStrata-Public-Id"] = public_id
                    return response
            chrome = _chrome_html(
                inner_html=body.decode("utf-8", errors="replace"),
                report_type=str(record.get("report_type")),
                generated_at=record.get("generated_at"),
                engine_version=record.get("engine_version"),
                public_id=public_id,
            )
            response = Response(
                content=chrome.encode("utf-8"),
                status_code=200,
                media_type="text/html; charset=utf-8",
            )

        max_age = int(self._policy.cache_max_age_seconds)
        response.headers["Cache-Control"] = f"private, max-age={max_age}, must-revalidate"
        response.headers["X-Robots-Tag"] = "noindex"
        if context.request_id:
            response.headers["X-Request-Id"] = context.request_id
        # Never expose bucket/key.
        meta = public_safe_metadata(record)
        response.headers["X-CodeStrata-Report-Type"] = str(meta.get("report_type") or "")
        response.headers["X-CodeStrata-Public-Id"] = public_id
        return response

    def handle_revoke(self, context: RequestContext) -> Response:
        if not self._available:
            return self._unavailable(context)
        principal = context.authenticated_client
        if principal is None:
            return build_error_response(
                ERROR_AUTHENTICATION_REQUIRED,
                http_status=401,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        public_id = (context.path_params or {}).get("public_id") or ""
        try:
            public_id = validate_public_report_id(public_id)
        except ValueError:
            return build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        record = self._store.get_json(_public_meta_key(public_id))
        if record is None:
            return build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        owner_ref = _owner_ref(principal)
        if record.get("owner_client_ref") != owner_ref:
            return build_error_response(
                ERROR_FORBIDDEN,
                http_status=403,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        record = dict(record)
        record["status"] = STATUS_REVOKED
        record["revoked_at"] = float(self._clock())
        self._store.put_json(_public_meta_key(public_id), record)

        # Drop from logical index if this id is current/previous.
        report_type = str(record.get("report_type"))
        logical_key = str(record.get("logical_identity_key"))
        logic = self._store.get_json(_logic_key(report_type, logical_key)) or {}
        changed = False
        if logic.get("current_public_id") == public_id:
            logic["current_public_id"] = None
            changed = True
        if logic.get("previous_public_id") == public_id:
            logic["previous_public_id"] = None
            changed = True
        if changed:
            self._store.put_json(_logic_key(report_type, logical_key), logic)

        prefix = str(record.get("artifact_prefix") or "")
        if prefix:
            self._store.delete_prefix(prefix)

        return build_json_response(
            {
                "api_version": context.api_version,
                "public_id": public_id,
                "status": STATUS_REVOKED,
            },
            status_code=200,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    def _rotate_and_promote(
        self,
        *,
        report_type: str,
        logical_key: str,
        artifacts: dict[str, bytes],
        public_id: str,
        owner_ref: str,
    ) -> None:
        logic_path = _logic_key(report_type, logical_key)
        logic = self._store.get_json(logic_path) or {
            "report_type": report_type,
            "logical_identity_key": logical_key,
            "current_public_id": None,
            "previous_public_id": None,
        }
        old_current = logic.get("current_public_id")
        old_previous = logic.get("previous_public_id")

        # Prune oldest previous (third version becomes inaccessible).
        if old_previous:
            self._revoke_public_id(str(old_previous), delete_artifacts=True)

        # Move old current → previous.
        if old_current:
            old_rec = self._store.get_json(_public_meta_key(str(old_current)))
            if old_rec and old_rec.get("status") == STATUS_PUBLISHED:
                old_prefix = str(old_rec.get("artifact_prefix") or "")
                new_prev_prefix = _artifact_prefix(
                    report_type, logical_key, SLOT_PREVIOUS
                )
                self._store.delete_prefix(new_prev_prefix)
                for key in self._store.list_keys(old_prefix):
                    name = key[len(old_prefix) :]
                    body = self._store.get_bytes(key)
                    if body is None:
                        continue
                    self._store.put_bytes(
                        f"{new_prev_prefix}{name}",
                        body,
                        content_type=_content_type_for(name),
                    )
                self._store.delete_prefix(old_prefix)
                old_rec = dict(old_rec)
                old_rec["slot"] = SLOT_PREVIOUS
                old_rec["artifact_prefix"] = new_prev_prefix
                self._store.put_json(_public_meta_key(str(old_current)), old_rec)
                logic["previous_public_id"] = old_current
            else:
                logic["previous_public_id"] = None
        else:
            logic["previous_public_id"] = None

        current_prefix = _artifact_prefix(report_type, logical_key, SLOT_CURRENT)
        self._store.delete_prefix(current_prefix)
        for name, body in artifacts.items():
            self._store.put_bytes(
                f"{current_prefix}{name}",
                body,
                content_type=_content_type_for(name),
            )

        generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._clock()))
        engine_version = None
        json_name = (
            "assessment.json"
            if report_type == REPORT_TYPE_ASSESSMENT
            else "engineering-intelligence-report.json"
        )
        raw_json = artifacts.get(json_name)
        if raw_json:
            try:
                import json as _json

                parsed = _json.loads(raw_json.decode("utf-8"))
                if isinstance(parsed, dict):
                    engine_version = (
                        parsed.get("engine_version")
                        or parsed.get("codestrata_version")
                        or (parsed.get("meta") or {}).get("engine_version")
                    )
                    generated_at = (
                        parsed.get("generated_at")
                        or parsed.get("created_at")
                        or generated_at
                    )
            except Exception:  # noqa: BLE001
                pass

        record = {
            "public_id": public_id,
            "status": STATUS_PUBLISHED,
            "report_type": report_type,
            "logical_identity_type": (
                LOGICAL_REPOSITORY
                if report_type == REPORT_TYPE_ASSESSMENT
                else LOGICAL_PORTFOLIO
            ),
            "logical_identity_key": logical_key,
            "slot": SLOT_CURRENT,
            "owner_client_ref": owner_ref,
            "artifact_prefix": current_prefix,
            "generated_at": generated_at,
            "engine_version": engine_version,
            "artifacts": sorted(artifacts.keys()),
            "published_at": generated_at,
            "verification_status": VERIFICATION_PENDING,
        }
        self._store.put_json(_public_meta_key(public_id), record)
        logic["current_public_id"] = public_id
        logic["report_type"] = report_type
        logic["logical_identity_key"] = logical_key
        self._store.put_json(logic_path, logic)

        # Private temporary validation registry (Insights-only; not public).
        identity_type = (
            LOGICAL_REPOSITORY
            if report_type == REPORT_TYPE_ASSESSMENT
            else LOGICAL_PORTFOLIO
        )
        self._store.put_json(
            validation_entry_key(public_id),
            build_validation_entry(
                public_id=public_id,
                public_url=public_report_url(public_id),
                report_type=report_type,
                logical_identity_key=logical_key,
                logical_identity_type=identity_type,
                published_at=generated_at,
                verification_status=VERIFICATION_PENDING,
            ),
        )

    def _revoke_public_id(self, public_id: str, *, delete_artifacts: bool) -> None:
        record = self._store.get_json(_public_meta_key(public_id))
        if record is None:
            return
        record = dict(record)
        record["status"] = STATUS_REVOKED
        record["revoked_at"] = float(self._clock())
        self._store.put_json(_public_meta_key(public_id), record)
        if delete_artifacts:
            prefix = str(record.get("artifact_prefix") or "")
            if prefix:
                self._store.delete_prefix(prefix)

    def list_published_registry(self) -> dict[str, list[dict[str, Any]]]:
        """Safe Insights projection: current/previous public URLs only (no S3 keys)."""

        if not self._available:
            return {"assessments": [], "engineering_intelligence": []}

        verification_by_id = self._verification_index()
        assessments: list[dict[str, Any]] = []
        eirs: list[dict[str, Any]] = []
        for key in self._store.list_keys("metadata/logic/"):
            if not key.endswith(".json"):
                continue
            logic = self._store.get_json(key)
            if not isinstance(logic, dict):
                continue
            report_type = str(logic.get("report_type") or "")
            logical_key = str(logic.get("logical_identity_key") or "")
            if not logical_key:
                continue
            current_id = logic.get("current_public_id")
            previous_id = logic.get("previous_public_id")
            current_status, current_url = self._safe_slot(current_id)
            previous_status, previous_url = self._safe_slot(previous_id)
            if current_id is None and previous_id is None:
                continue
            current_verify = verification_by_id.get(str(current_id or "")) or {}
            entry: dict[str, Any] = {
                "current_public_url": current_url,
                "current_status": current_status,
                "last_verified_status": current_verify.get("verified_http_status"),
                "verification_status": current_verify.get("verification_status"),
                "published_at": current_verify.get("published_at"),
                "public_report_id": current_id,
                "previous_public_url": previous_url,
                "previous_status": previous_status,
            }
            if report_type == REPORT_TYPE_ASSESSMENT:
                entry["repository_id"] = logical_key
                entry["report_type"] = REPORT_TYPE_ASSESSMENT
                assessments.append(entry)
            elif report_type == REPORT_TYPE_EIR:
                entry["portfolio_id"] = logical_key
                entry["report_type"] = REPORT_TYPE_EIR
                eirs.append(entry)

        assessments.sort(key=lambda e: str(e.get("repository_id") or ""))
        eirs.sort(key=lambda e: str(e.get("portfolio_id") or ""))
        return {
            "assessments": assessments,
            "engineering_intelligence": eirs,
        }

    def list_validation_registry(
        self,
        *,
        limit: int = 50,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Paginated private validation registry for authenticated Insights."""

        if not self._available:
            return {
                "items": [],
                "next_cursor": None,
                "limit": sanitize_list_limit(limit),
                "temporary": True,
                "purpose": "temporary_community_validation",
            }

        capped = sanitize_list_limit(limit)
        keys = [
            k
            for k in self._store.list_keys(VALIDATION_ENTRIES_PREFIX)
            if k.endswith(".json")
        ]
        # Newest published_at first; fall back to key order.
        entries: list[dict[str, Any]] = []
        for key in keys:
            row = self._store.get_json(key)
            if isinstance(row, dict) and row.get("public_report_id"):
                entries.append(row)
        entries.sort(
            key=lambda e: (
                str(e.get("published_at") or ""),
                str(e.get("public_report_id") or ""),
            ),
            reverse=True,
        )

        start = 0
        if cursor:
            for idx, row in enumerate(entries):
                if str(row.get("public_report_id")) == cursor:
                    start = idx + 1
                    break
        page = entries[start : start + capped]
        next_cursor = None
        if start + capped < len(entries) and page:
            next_cursor = str(page[-1].get("public_report_id") or "") or None

        # Strip internal-only fields that must never leave the private API? Keep
        # display-safe fields only (no artifact prefixes / owner refs).
        safe_items: list[dict[str, Any]] = []
        for row in page:
            safe_items.append(
                {
                    "public_report_id": row.get("public_report_id"),
                    "public_url": row.get("public_url"),
                    "report_type": row.get("report_type"),
                    "display_identity": row.get("display_identity")
                    or row.get("logical_identity_key"),
                    "logical_identity_key": row.get("logical_identity_key"),
                    "logical_identity_type": row.get("logical_identity_type"),
                    "published_at": row.get("published_at"),
                    "verification_status": row.get("verification_status"),
                    "verified_http_status": row.get("verified_http_status"),
                    "verified_at": row.get("verified_at"),
                    "temporary": True,
                }
            )
        return {
            "items": safe_items,
            "next_cursor": next_cursor,
            "limit": capped,
            "temporary": True,
            "purpose": "temporary_community_validation",
            "note": (
                "Internal Community validation tooling only. Opaque public URLs; "
                "not a permanent product surface."
            ),
        }

    def handle_verification(self, context: RequestContext) -> Response:
        """Community-authenticated confirmation after independent public GET verify."""

        if not self._available:
            return self._unavailable(context)
        if context.authenticated_client is None:
            return build_error_response(
                ERROR_AUTHENTICATION_REQUIRED,
                http_status=401,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        public_id = (context.path_params or {}).get("public_id") or ""
        try:
            public_id = validate_public_report_id(public_id)
        except ValueError:
            return build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        from codestrata_platform.community_cloud_api.reports.models import (
            ReportVerificationRequest,
        )

        req = context.validated_request
        if not isinstance(req, ReportVerificationRequest):
            return build_error_response(
                ERROR_INVALID_REQUEST_SCHEMA,
                http_status=422,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        status = req.verification_status
        http_code = req.http_status

        public_meta = self._store.get_json(_public_meta_key(public_id))
        if public_meta is None:
            return build_error_response(
                ERROR_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        verified_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._clock()))
        public_meta = dict(public_meta)
        public_meta["verification_status"] = status
        public_meta["verified_http_status"] = http_code
        public_meta["verified_at"] = verified_at if status == VERIFICATION_VERIFIED else None
        self._store.put_json(_public_meta_key(public_id), public_meta)

        entry = self._store.get_json(validation_entry_key(public_id))
        if not isinstance(entry, dict):
            entry = build_validation_entry(
                public_id=public_id,
                public_url=public_report_url(public_id),
                report_type=str(public_meta.get("report_type") or REPORT_TYPE_ASSESSMENT),
                logical_identity_key=str(public_meta.get("logical_identity_key") or ""),
                logical_identity_type=str(
                    public_meta.get("logical_identity_type") or LOGICAL_REPOSITORY
                ),
                published_at=str(public_meta.get("published_at") or verified_at),
                verification_status=status,
                verified_http_status=http_code,
                verified_at=verified_at if status == VERIFICATION_VERIFIED else None,
            )
        else:
            entry = dict(entry)
            entry["verification_status"] = status
            entry["verified_http_status"] = http_code
            entry["verified_at"] = verified_at if status == VERIFICATION_VERIFIED else None
            if status == VERIFICATION_FAILED:
                entry["verified_at"] = None
        self._store.put_json(validation_entry_key(public_id), entry)

        return build_json_response(
            {
                "api_version": context.api_version,
                "public_id": public_id,
                "verification_status": status,
                "verified_http_status": http_code,
                "verified_at": entry.get("verified_at"),
                "temporary": True,
            },
            status_code=200,
            api_version=context.api_version,
            request_id=context.request_id,
        )

    def _verification_index(self) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for key in self._store.list_keys(VALIDATION_ENTRIES_PREFIX):
            if not key.endswith(".json"):
                continue
            row = self._store.get_json(key)
            if isinstance(row, dict) and row.get("public_report_id"):
                out[str(row["public_report_id"])] = row
        return out

    def handle_feedback(self, context: RequestContext) -> Response:
        """Public voluntary Yes/No feedback — independent of telemetry consent."""

        if not self._available:
            return self._unavailable(context)
        public_id = (context.path_params or {}).get("public_id") or ""
        try:
            public_id = validate_public_report_id(public_id)
        except ValueError:
            return build_error_response(
                ERROR_REPORT_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        req = context.validated_request
        if not isinstance(req, ReportFeedbackRequest):
            return build_error_response(
                ERROR_INVALID_REQUEST_SCHEMA,
                http_status=422,
                api_version=context.api_version,
                request_id=context.request_id,
            )
        record = self._store.get_json(_public_meta_key(public_id))
        if record is None or str(record.get("status") or "") != STATUS_PUBLISHED:
            return build_error_response(
                ERROR_REPORT_NOT_FOUND,
                http_status=404,
                api_version=context.api_version,
                request_id=context.request_id,
            )

        vote_key = feedback_vote_key(
            public_id=public_id, respondent_token=req.respondent_token
        )
        prior = self._store.get_json(vote_key)
        prior_useful = None
        if isinstance(prior, dict):
            maybe = str(prior.get("useful") or "").strip().lower()
            if maybe in {"yes", "no"}:
                prior_useful = maybe

        summary = self._store.get_json(FEEDBACK_SUMMARY_KEY) or empty_feedback_summary()
        if not isinstance(summary, dict):
            summary = empty_feedback_summary()
        next_summary, outcome = apply_feedback_vote(
            summary=summary,
            prior_useful=prior_useful,
            new_useful=req.useful,
        )
        if outcome != "unchanged":
            self._store.put_json(
                vote_key,
                {
                    "schema_version": "1.0",
                    "useful": req.useful,
                    "updated_at": next_summary.get("updated_at"),
                },
            )
            self._store.put_json(FEEDBACK_SUMMARY_KEY, next_summary)

        return build_json_response(
            {
                "accepted": True,
                "useful": req.useful,
                "outcome": outcome,
            },
            status_code=200,
            api_version=context.api_version,
            request_id=context.request_id,
            extra_headers={
                "Cache-Control": "no-store",
                "Access-Control-Allow-Origin": "https://reports.codestrata.ai",
                "Vary": "Origin",
                "Access-Control-Allow-Methods": "POST,OPTIONS",
                "Access-Control-Allow-Headers": "Accept,Content-Type",
            },
        )

    def community_sentiment_summary(self) -> dict[str, Any]:
        """Aggregate Yes/No feedback counts for Insights (no respondent identities)."""

        if not self._available:
            return empty_feedback_summary()
        summary = self._store.get_json(FEEDBACK_SUMMARY_KEY)
        if not isinstance(summary, dict):
            return empty_feedback_summary()
        positive = int(summary.get("positive_responses") or 0)
        negative = int(summary.get("negative_responses") or 0)
        return {
            "schema_version": "1.0",
            "positive_responses": max(0, positive),
            "negative_responses": max(0, negative),
            "total_responses": max(0, positive) + max(0, negative),
            "updated_at": summary.get("updated_at"),
        }

    def _safe_slot(
        self, public_id: object
    ) -> tuple[str | None, str | None]:
        if not public_id:
            return None, None
        pid = str(public_id)
        record = self._store.get_json(_public_meta_key(pid))
        if record is None:
            return STATUS_REVOKED, public_report_url(pid)
        status = str(record.get("status") or STATUS_REVOKED)
        if status == STATUS_REVOKED:
            return STATUS_REVOKED, public_report_url(pid)
        return status, public_report_url(pid)

    def _unavailable(self, context: RequestContext) -> Response:
        return build_error_response(
            ERROR_REPORT_STORE_UNAVAILABLE,
            http_status=503,
            api_version=context.api_version,
            request_id=context.request_id,
        )


__all__ = ["ReportPublishingService"]
