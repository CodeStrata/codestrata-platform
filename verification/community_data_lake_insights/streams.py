"""Stream register / EventStream source audit."""

from __future__ import annotations

from pathlib import Path

from verification.community_data_lake_insights.contract import (
    ENUMS_PY,
    STREAM_REGISTER,
)
from verification.community_data_lake_insights.helpers import check, load_json, read_text
from verification.community_data_lake_insights.models import CheckResult, Defect

EXPECTED_STREAMS = (
    "telemetry",
    "assessment_metadata",
    "cli_event",
    "extension_event",
    "ai_usage",
)


def check_streams(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    register = load_json(monorepo / STREAM_REGISTER)
    entries = register.get("entries") or []
    names = [e.get("stream") for e in entries if isinstance(e, dict)]
    summary = {
        "schema": register.get("schema"),
        "streams": names,
        "extension_event_no_fabricated_traffic": True,
    }

    for stream in EXPECTED_STREAMS:
        ok = stream in names
        checks.append(check(f"streams:register_{stream}", ok, stream, "streams"))
        if not ok:
            defects.append(
                Defect("missing_stream", f"streams:register_{stream}", stream, "absent")
            )

    enums_text = read_text(monorepo / ENUMS_PY)
    member_map = {
        "telemetry": "TELEMETRY",
        "assessment_metadata": "ASSESSMENT_METADATA",
        "cli_event": "CLI_EVENT",
        "extension_event": "EXTENSION_EVENT",
        "ai_usage": "AI_USAGE",
    }
    for stream in EXPECTED_STREAMS:
        member = member_map[stream]
        ok = member in enums_text and f'"{stream}"' in enums_text
        checks.append(check(f"streams:enum_{stream}", ok, member, "streams"))
        if not ok:
            defects.append(
                Defect("enum_missing", f"streams:enum_{stream}", member, "absent")
            )

    # extension_event must remain contract-only (no fabricated traffic)
    ext = next((e for e in entries if e.get("stream") == "extension_event"), {})
    status = str(ext.get("validation_status") or "")
    no_fab = "no_fabricated" in status or "contract_only" in status
    summary["extension_event_no_fabricated_traffic"] = no_fab
    checks.append(
        check(
            "streams:extension_event_contract_only",
            no_fab,
            status or "missing",
            "streams",
        )
    )
    if not no_fab:
        defects.append(
            Defect(
                "extension_event_fabricated",
                "streams:extension_event_contract_only",
                "contract_only_no_fabricated_traffic",
                status,
            )
        )
    return checks, defects, summary
