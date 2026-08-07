"""Active and retired client inventories (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.contract import (
    ACTIVE_CLIENTS,
    RETIRED_HISTORICAL_CLIENTS,
    TELEMETRY_OTHER_EXTENSION,
)
from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def active_client_inventory() -> list[str]:
    # other_extension remains on the public telemetry contract only.
    return sorted({*ACTIVE_CLIENTS, TELEMETRY_OTHER_EXTENSION})


def retired_client_inventory() -> list[str]:
    return sorted(RETIRED_HISTORICAL_CLIENTS)


def check_active_clients(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    auth = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "authentication"
        / "models.py"
    ).read_text(encoding="utf-8")
    ext = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "extension_events"
        / "enums.py"
    ).read_text(encoding="utf-8")
    ai = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "ai_usage"
        / "enums.py"
    ).read_text(encoding="utf-8")

    # Active allowlists must not include cursor_extension as ALLOWED_* value set member
    # after ACTIVE_*/ALLOWED_* assignment lines — check tuple contents of ACTIVE_*.
    active_ext_ok = 'ACTIVE_EXTENSION_CLIENTS: tuple[str, ...] = (VSCODE_EXTENSION_CLIENT,)' in ext
    active_ai_ok = "AI_USAGE_CLIENT_CURSOR" not in ai.split("ACTIVE_AI_USAGE_CLIENTS")[1].split(
        "HISTORICAL_AI_USAGE_CLIENTS"
    )[0]
    active_auth_ok = "CLIENT_TYPE_CURSOR" not in auth.split("ACTIVE_CLIENT_TYPES")[1].split(
        "HISTORICAL_CLIENT_TYPES"
    )[0]

    checks.append(
        CheckResult(
            "active:extension_clients_vscode_only",
            ok=active_ext_ok,
            detail="ACTIVE_EXTENSION_CLIENTS=vscode_extension",
            category="active",
        )
    )
    checks.append(
        CheckResult(
            "active:ai_usage_clients_exclude_cursor",
            ok=active_ai_ok,
            detail="ACTIVE_AI_USAGE_CLIENTS excludes cursor",
            category="active",
        )
    )
    checks.append(
        CheckResult(
            "active:auth_clients_exclude_cursor",
            ok=active_auth_ok,
            detail="ACTIVE_CLIENT_TYPES excludes cursor",
            category="active",
        )
    )
    checks.append(
        CheckResult(
            "active:cli_and_vscode_present",
            ok="codestrata_cli" in auth and "vscode_extension" in auth and "vscode_extension" in ext,
            detail="CLI and VS Code remain active",
            category="active",
        )
    )

    for name, ok in (
        ("extension", active_ext_ok),
        ("ai_usage", active_ai_ok),
        ("auth", active_auth_ok),
    ):
        if not ok:
            defects.append(
                Defect(
                    "active-client vocabulary defect",
                    name,
                    "cursor absent from active allowlist",
                    "cursor still active",
                )
            )
    return checks, defects


def check_retired_clients(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "retired_clients.py"
    )
    hist = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "historical_client_compatibility.py"
    )
    ext = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "extension_events"
        / "enums.py"
    ).read_text(encoding="utf-8")

    ok_policy = policy.is_file()
    ok_hist = hist.is_file()
    ok_hist_tuple = "HISTORICAL_EXTENSION_CLIENTS" in ext and "CURSOR_EXTENSION_CLIENT" in ext
    checks.append(
        CheckResult(
            "retired:policy_module_present",
            ok=ok_policy,
            detail="community-retired-client-policy:1.0",
            category="retired",
        )
    )
    checks.append(
        CheckResult(
            "retired:historical_helpers_present",
            ok=ok_hist,
            detail="historical_client_compatibility module",
            category="retired",
        )
    )
    checks.append(
        CheckResult(
            "retired:historical_extension_clients",
            ok=ok_hist_tuple,
            detail="HISTORICAL_EXTENSION_CLIENTS retains cursor_extension",
            category="retired",
        )
    )
    if not (ok_policy and ok_hist and ok_hist_tuple):
        defects.append(
            Defect(
                "historical-deserialization defect",
                "retired_clients",
                "policy+helpers+historical tuple",
                "missing",
            )
        )
    return checks, defects
