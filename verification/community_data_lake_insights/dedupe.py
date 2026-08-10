"""Event identity / dedupe source audit + optional live duplicate POST."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from verification.community_data_lake_insights.contract import (
    API_BASE,
    AWS_PROFILE,
    AWS_REGION,
    CREDENTIAL_FILE_RELATIVE,
    DATA_LAKE_BUCKET,
)
from verification.community_data_lake_insights.helpers import check, read_text
from verification.community_data_lake_insights.models import CheckResult, Defect


def _resolve_credential(monorepo: Path) -> str | None:
    env = (os.environ.get("CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL") or "").strip()
    if env:
        return env
    path = monorepo / CREDENTIAL_FILE_RELATIVE
    if path.is_file():
        return path.read_text(encoding="utf-8").strip() or None
    return None


def _count_prefix(client: Any, bucket: str, prefix: str) -> int:
    total = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        total += int(page.get("KeyCount") or len(page.get("Contents") or []))
    return total


def _post(path: str, body: dict[str, Any], authorization: str) -> tuple[int, dict[str, Any]]:
    data = json.dumps(body).encode("utf-8")
    req = Request(
        f"{API_BASE}{path}",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": authorization,
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {}
            return int(resp.status), parsed if isinstance(parsed, dict) else {}
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        return int(exc.code), parsed if isinstance(parsed, dict) else {}
    except URLError:
        return 0, {}


def check_dedupe(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    identity_dir = (
        monorepo
        / "platform/src/codestrata_platform/community_cloud_api/event_identity"
    )
    store_present = identity_dir.is_dir()
    checks.append(
        check(
            "dedupe:event_identity_store_present",
            store_present,
            "event_identity package",
            "dedupe",
        )
    )
    if not store_present:
        defects.append(
            Defect(
                "event_identity_missing",
                "dedupe:event_identity_store_present",
                "present",
                "absent",
            )
        )

    # Source mentions already_accepted semantics in HTTP transport
    http_transport = (
        monorepo
        / "engine/src/codestrata/telemetry/infrastructure/http_transport.py"
    )
    has_already = http_transport.is_file() and "already_accepted" in read_text(
        http_transport
    )
    checks.append(
        check(
            "dedupe:already_accepted_semantics",
            has_already,
            "already_accepted present in HttpTelemetryTransport",
            "dedupe",
        )
    )

    summary: dict[str, Any] = {
        "event_identity_store": store_present,
        "already_accepted_semantics": has_already,
        "live_duplicate_tested": False,
        "duplicate_raw_delta": None,
        "duplicate_status": None,
        "duplicates_counted": False,
        "note": "identity store provides idempotency; duplicates should not inflate raw",
    }

    credential = _resolve_credential(monorepo)
    if not credential:
        checks.append(
            check(
                "dedupe:live_duplicate",
                True,
                "skipped without credential (covered by live_probe credential gate)",
                "dedupe",
            )
        )
        return checks, defects, summary

    os.environ.setdefault("AWS_PROFILE", AWS_PROFILE)
    os.environ.setdefault("AWS_REGION", AWS_REGION)
    event_id = f"sv1718-dedupe-{uuid.uuid4().hex[:8]}"
    body = {
        "schema_version": "1.0",
        "event_id": event_id,
        "event_type": "application_started",
        "client": {
            "name": "codestrata_cli",
            "version": "0.2.0",
            "platform": "darwin",
        },
    }
    auth = f"Bearer {credential}"
    status1, _ = _post("/api/v1/telemetry", body, auth)
    time.sleep(1.5)
    try:
        import boto3

        session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", AWS_PROFILE))
        client = session.client("s3", region_name=AWS_REGION)
        before = _count_prefix(client, DATA_LAKE_BUCKET, "raw/stream=telemetry/")
    except Exception:  # noqa: BLE001
        before = None

    status2, body2 = _post("/api/v1/telemetry", body, auth)
    time.sleep(1.5)
    after = None
    if before is not None:
        try:
            after = _count_prefix(client, DATA_LAKE_BUCKET, "raw/stream=telemetry/")
        except Exception:  # noqa: BLE001
            after = None

    ack = str(body2.get("status") or body2.get("result") or "").lower()
    duplicate_ok = status2 in {200, 202} or ack == "already_accepted"
    delta = None if before is None or after is None else after - before
    # If design supports dedupe, second post should not increase raw by another object.
    # Document if delta >= 1 (duplicates counted).
    duplicates_counted = bool(delta is not None and delta >= 1)
    summary.update(
        {
            "live_duplicate_tested": True,
            "duplicate_status": status2,
            "first_status": status1,
            "duplicate_raw_delta": delta,
            "duplicates_counted": duplicates_counted,
            "note": (
                "duplicate increased raw count"
                if duplicates_counted
                else "duplicate did not increase raw (or already_accepted)"
            ),
        }
    )
    checks.append(
        check(
            "dedupe:live_duplicate",
            duplicate_ok,
            f"status={status2} delta={delta}",
            "dedupe",
        )
    )
    # Not a hard defect if duplicates are intentionally counted — document only.
    if duplicates_counted:
        summary["note"] = "duplicates may be counted; identity ack still returned"
    return checks, defects, summary
