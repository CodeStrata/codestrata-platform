"""Installation identity audit helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_event_coverage.inventory import exists, read_text
from verification.community_insights_event_coverage.policy import load_coverage_policy


def identity_audit(monorepo: Path) -> dict[str, Any]:
    policy = load_coverage_policy(monorepo)
    identity = dict(policy.get("installation_identity") or {})
    engine = exists(
        monorepo,
        "engine/src/codestrata/telemetry/analytics/installation_identity.py",
    )
    vscode_forbid = "installation_id" in read_text(
        monorepo, "vscode-plugin/src/telemetry/analytics/schema.ts"
    ).lower() or "FORBIDDEN" in read_text(
        monorepo, "vscode-plugin/src/telemetry/analytics/schema.ts"
    )
    return {
        **identity,
        "engine_identity_module_present": engine,
        "vscode_schema_mentions_forbid_or_identity": vscode_forbid,
        "redesign_forbidden_in_15_3": True,
    }
