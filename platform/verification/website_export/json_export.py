"""JSON export verification."""

from __future__ import annotations

import json
import re

from codestrata_platform.intelligence_reporting.application.website_export import (
    JSON_FILENAME,
    WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
)

from verification.website_export.contract import UNSUPPORTED_SCORE_FRAGMENTS
from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_json_export(verified: VerifiedExportInput) -> list[CheckResult]:
    raw = verified.bundle.json_bytes
    text = raw.decode("utf-8")
    payload = json.loads(text)
    meta = verified.bundle.document.export_metadata
    assert meta is not None
    reserialized = (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    lowered = text.lower()
    checks = [
        CheckResult(
            name="json:filename_contract",
            ok=JSON_FILENAME == "engineering-intelligence-report.json",
            detail=JSON_FILENAME,
            category="json",
        ),
        CheckResult(
            name="json:utf8_object",
            ok=isinstance(payload, dict) and raw.endswith(b"\n"),
            detail=f"bytes={len(raw)}",
            category="json",
        ),
        CheckResult(
            name="json:sorted_keys_stable",
            ok=reserialized == raw,
            detail="sort_keys+indent=2",
            category="json",
        ),
        CheckResult(
            name="json:schema_version",
            ok=payload.get("export_schema_version") == WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
            detail=str(payload.get("export_schema_version")),
            category="json",
        ),
        CheckResult(
            name="json:export_id",
            ok=payload.get("export_metadata", {}).get("export_id") == meta.export_id,
            detail="export id present",
            category="json",
        ),
        CheckResult(
            name="json:source_report_id",
            ok=payload.get("report_id") == verified.report.report_id.value,
            detail=str(payload.get("report_id")),
            category="json",
        ),
        CheckResult(
            name="json:dataset_summary_present",
            ok=isinstance(payload.get("dataset_summary"), dict)
            and int(payload["dataset_summary"].get("repository_count", -1)) == 5,
            detail=str(payload.get("dataset_summary", {}).get("repository_count")),
            category="json",
            scenario="A",
        ),
        CheckResult(
            name="json:repo_count_reconcile",
            ok=int(payload.get("dataset_summary", {}).get("repository_count", -1)) == 5,
            detail=str(payload.get("dataset_summary", {}).get("repository_count")),
            category="json",
            scenario="A",
        ),
        CheckResult(
            name="json:drilldown_count_reconcile",
            ok=len(payload.get("repository_drilldowns", [])) == 5,
            detail=str(len(payload.get("repository_drilldowns", []))),
            category="json",
            scenario="A",
        ),
        CheckResult(
            name="json:no_paths_or_file_urls",
            ok="/Users/" not in text and "file://" not in lowered and "/home/" not in text,
            detail="path-free",
            category="json",
        ),
        CheckResult(
            name="json:no_unsupported_scores",
            ok=not any(frag in lowered for frag in UNSUPPORTED_SCORE_FRAGMENTS),
            detail="no maturity/health/readiness",
            category="json",
        ),
        CheckResult(
            name="json:no_nan",
            ok="NaN" not in text and "Infinity" not in text,
            detail="allow_nan=False",
            category="json",
        ),
        CheckResult(
            name="json:no_script_injection_fields",
            ok="<script" not in lowered,
            detail="no script markers",
            category="json",
        ),
    ]
    # Entity ref IDs may be UUID-shaped; repository aliases must not be raw UUIDs.
    aliases = [
        item.repository_alias
        for item in verified.bundle.document.repository_drilldowns
    ]
    uuid_alias = any(
        re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            alias,
            flags=re.I,
        )
        for alias in aliases
    )
    checks.append(
        CheckResult(
            name="json:no_uuid_repository_aliases",
            ok=not uuid_alias,
            detail=f"aliases={len(aliases)}",
            category="json",
        )
    )
    return checks
