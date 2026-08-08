"""Static checks for Slice 16.1 repository inventory."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from verification.repository_inventory.contract import (
    CLASSIFICATIONS,
    INVENTORY_AREAS,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    POLICY_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.repository_inventory.models import CheckResult, Defect, InventoryEntry


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "inventory",
) -> None:
    checks.append(CheckResult(check_id, ok, detail, category))
    if not ok:
        defects.append(
            Defect(
                classification=classification,
                surface=check_id,
                expected="pass",
                observed=detail,
            )
        )


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    _add(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    policy: dict = {}
    if path.is_file():
        policy = json.loads(path.read_text(encoding="utf-8"))
    _add(
        checks,
        defects,
        "policy:id",
        policy.get("policy_id") == POLICY_ID,
        str(policy.get("policy_id")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:version",
        str(policy.get("policy_version")) == POLICY_VERSION,
        str(policy.get("policy_version")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:schema",
        policy.get("schema") == POLICY_SCHEMA,
        str(policy.get("schema")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:audit_only",
        policy.get("audit_only") is True,
        str(policy.get("audit_only")),
        "policy",
    )
    for flag in (
        "delete_forbidden_in_16_1",
        "rename_forbidden_in_16_1",
        "move_forbidden_in_16_1",
        "runtime_behavior_change_forbidden",
    ):
        _add(checks, defects, f"policy:{flag}", policy.get(flag) is True, str(policy.get(flag)), "policy")
    _add(
        checks,
        defects,
        "policy:documentation_cleanup_in_16_2_or_deferred",
        policy.get("documentation_cleanup_in_16_2") is True
        or policy.get("cleanup_actions_deferred_to_16_2") is True,
        str(
            {
                "documentation_cleanup_in_16_2": policy.get("documentation_cleanup_in_16_2"),
                "cleanup_actions_deferred_to_16_2": policy.get("cleanup_actions_deferred_to_16_2"),
            }
        ),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_5_true",
        policy.get("start_slice_16_5", False) is True,
        str(policy.get("start_slice_16_5", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_6_true",
        policy.get("start_slice_16_6", False) is True,
        str(policy.get("start_slice_16_6", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_7_true",
        policy.get("start_slice_16_7", False) is True,
        str(policy.get("start_slice_16_7", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_8_true",
        policy.get("start_slice_16_8", False) is True,
        str(policy.get("start_slice_16_8", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_9_true",
        policy.get("start_slice_16_9", False) is True,
        str(policy.get("start_slice_16_9", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_10_true",
        policy.get("start_slice_16_10", False) is True,
        str(policy.get("start_slice_16_10", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_epic_17_false",
        policy.get("start_epic_17", False) is False,
        str(policy.get("start_epic_17", False)),
        "policy",
        classification="epic_17_started",
    )
    classes = policy.get("classifications") or []
    _add(
        checks,
        defects,
        "policy:classifications_complete",
        set(classes) == set(CLASSIFICATIONS),
        f"count={len(classes)}",
        "policy",
    )
    areas = policy.get("inventory_areas") or []
    _add(
        checks,
        defects,
        "policy:inventory_areas_complete",
        set(areas) == set(INVENTORY_AREAS),
        f"count={len(areas)}",
        "policy",
    )
    verification = policy.get("verification") or {}
    _add(
        checks,
        defects,
        "policy:verification_schema",
        verification.get("schema") == f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
        str(verification.get("schema")),
        "policy",
    )
    return checks, defects, policy


def check_inventory_coverage(
    entries: list[InventoryEntry],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(checks, defects, "inventory:non_empty", len(entries) > 0, str(len(entries)), "inventory")
    areas_present = {e.area for e in entries}
    for area in (
        "engine",
        "platform",
        "infrastructure",
        "vscode-plugin",
        "docs",
        "design-system",
        "verification",
        "tests",
        "reports",
    ):
        _add(
            checks,
            defects,
            f"inventory:area_{area}",
            area in areas_present or any(e.path == area or e.path.startswith(area + "/") for e in entries),
            "present" if area in areas_present else "missing",
            "inventory",
        )
    unknown = sorted({e.classification for e in entries} - set(CLASSIFICATIONS))
    _add(
        checks,
        defects,
        "inventory:classifications_known",
        not unknown,
        "ok" if not unknown else ",".join(unknown),
        "inventory",
    )
    return checks, defects


def check_no_cleanup_mutations(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Slice 16.2 package must not exist
    cleanup_pkg = monorepo / "verification" / "repository_cleanup"
    _add(
        checks,
        defects,
        "boundary:no_repository_cleanup_package",
        not cleanup_pkg.exists(),
        "absent" if not cleanup_pkg.exists() else "present",
        "boundary",
        classification="slice_16_5_started",
    )
    sv167 = monorepo / "reports" / "verification" / "sv17-1"
    _add(
        checks,
        defects,
        "boundary:no_sv17_1_report",
        not sv167.exists(),
        "absent" if not sv167.exists() else "present",
        "boundary",
        classification="epic_17_started",
    )
    return checks, defects


def check_special_audits_present(special: dict) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    required = (
        "sqlite_databases",
        "legacy_aimf_references",
        "legacy_cursor_references",
        "duplicate_tokens_css",
        "dist_directories",
        "temp_or_junk_candidates",
        "duplicate_policies_or_schemas",
        "stale_markdown_candidates",
        "committed_node_modules_tracked",
    )
    for key in required:
        _add(
            checks,
            defects,
            f"special_audit:{key}_key",
            key in special,
            "present" if key in special else "missing",
            "special_audit",
        )
    return checks, defects


def check_git_tracked_node_modules(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tracked: list[str] = []
    try:
        proc = subprocess.run(
            ["git", "ls-files", "**/node_modules/**"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            tracked = sorted(line for line in proc.stdout.splitlines() if line.strip())
    except OSError:
        tracked = []
    _add(
        checks,
        defects,
        "git:no_tracked_node_modules",
        len(tracked) == 0,
        "none" if not tracked else f"count={len(tracked)}",
        "special_audit",
    )
    return checks, defects, tracked


def check_authoritative_tokens(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / "design-system" / "tokens" / "tokens.css"
    _add(
        checks,
        defects,
        "assets:authoritative_tokens_exist",
        path.is_file(),
        "design-system/tokens/tokens.css",
        "special_audit",
    )
    return checks, defects
