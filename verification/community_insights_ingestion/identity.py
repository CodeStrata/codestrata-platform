"""Installation identity rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_ingestion.inventory import exists
from verification.community_insights_ingestion.policy import load_ingestion_policy


def identity_rules(monorepo: Path) -> dict[str, Any]:
    policy = load_ingestion_policy(monorepo)
    return {
        **dict(policy.get("installation_identity") or {}),
        "vscode_reader_present": exists(
            monorepo, "vscode-plugin/src/communityCloud/installationIdentity.ts"
        ),
        "engine_identity_present": exists(
            monorepo,
            "engine/src/codestrata/telemetry/analytics/installation_identity.py",
        ),
    }
