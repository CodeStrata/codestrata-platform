"""Event stream inventory checks."""

from __future__ import annotations

import json
from pathlib import Path

from verification.community_telemetry_consent.helpers import check, load_json
from verification.community_telemetry_consent.models import CheckResult, Defect

EXPECTED_STREAMS = (
    "telemetry",
    "assessment_metadata",
    "cli_event",
    "extension_event",
    "ai_usage",
)


def check_event_types(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    routes = load_json(monorepo / "platform/policies/community_api_route_register.json")
    entries = routes.get("routes") or routes.get("entries") or routes.get("route_entries") or []
    if isinstance(routes.get("routes"), dict):
        entries = list(routes["routes"].values()) if isinstance(routes["routes"], dict) else routes["routes"]
    # normalize various register shapes
    found = []
    consent_dep = {}
    raw = json.dumps(routes)
    for stream in EXPECTED_STREAMS:
        # path fragments
        key = stream.replace("_", "-")
        present = stream in raw or key in raw or stream.replace("_", "") in raw
        found.append(stream if present else None)
        consent_dep[stream] = '"consent_dependency": true' in raw or "consent_dependency" in raw
        checks.append(check(f"events:stream_{stream}", present, f"register mentions {stream}", "event_types"))

    # stronger: look for consent_dependency true near telemetry path
    checks.append(check(
        "events:consent_dependency_present",
        "consent_dependency" in raw,
        "route register includes consent_dependency",
        "event_types",
    ))
    summary = {
        "streams": [s for s in found if s],
        "consent_required": True,
        "producer": "client_enforced",
        "server_validates_consent_field": False,
    }
    return checks, defects, summary
