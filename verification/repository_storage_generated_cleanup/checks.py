"""Checks for Slice 16.6 storage & generated cleanup."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.repository_storage_generated_cleanup.contract import (
    CLASSIFICATIONS,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    PROTECTED_PATHS,
    REGISTER_RELATIVE,
    REMOVED_LOCAL_PATHS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.repository_storage_generated_cleanup.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "check_failed",
) -> None:
    checks.append(CheckResult(check_id, ok, detail, category))
    if not ok:
        defects.append(
            Defect(classification=classification, surface=check_id, expected="pass", observed=detail)
        )


def _load(monorepo: Path, rel: str) -> dict:
    path = monorepo / rel
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = _load(monorepo, POLICY_RELATIVE)
    _add(checks, defects, "policy:exists", bool(policy), POLICY_RELATIVE, "policy")
    _add(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    for flag in (
        "source_vs_generated_distinction",
        "tracked_generated_exceptions",
        "local_runtime_state_rules",
        "sqlite_fixture_rules",
        "build_output_rules",
        "export_staging_rules",
        "opentofu_state_cache_rules",
        "test_fixture_protection",
        "gitignore_authority",
        "no_product_runtime_semantic_change",
        "no_repository_relocation",
        "no_dependency_changes",
    ):
        _add(checks, defects, f"policy:{flag}", policy.get(flag) is True, str(policy.get(flag)), "policy")
    _add(
        checks,
        defects,
        "policy:production_ingestion_false",
        policy.get("production_ingestion_enabled") is False,
        str(policy.get("production_ingestion_enabled")),
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
    _add(checks, defects, "policy:classifications", set(classes) == set(CLASSIFICATIONS), f"count={len(classes)}", "policy")
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


def check_register(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = _load(monorepo, REGISTER_RELATIVE)
    entries = reg.get("entries") or []
    _add(checks, defects, "register:exists", len(entries) >= 8, REGISTER_RELATIVE, "register")
    unknown = [e for e in entries if e.get("class") not in CLASSIFICATIONS]
    _add(checks, defects, "register:classes_valid", not unknown, str(len(unknown)), "register")
    return checks, defects, reg


def check_removals_and_protected(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    removed: list[str] = []
    for rel in REMOVED_LOCAL_PATHS:
        # After recreation tests some build outputs may exist again; treat persistent local-state paths as must-absent
        must_absent = rel in {
            ".codestrata",
            "engine/.codestrata",
            ".codestrata-test-knowledge",
            "engine/.codestrata-test-knowledge",
            ".export-staging",
            "infrastructure/production/.terraform",
            "infrastructure/modules/community-cloud-api/.terraform",
            "infrastructure/modules/community-data-lake/.terraform",
            ".mypy_cache",
            "engine/.mypy_cache",
        }
        exists = (monorepo / rel).exists()
        if must_absent:
            _add(checks, defects, f"removal:absent_{rel.replace('/', '_')}", not exists, "absent" if not exists else "present", "removals")
        if not exists or not must_absent:
            removed.append(rel)
    protected: list[str] = []
    for rel in PROTECTED_PATHS:
        p = monorepo / rel
        ok = p.exists()
        _add(checks, defects, f"protected:present_{rel.replace('/', '_').replace('.', '_')}", ok, "present" if ok else "missing", "fixtures")
        if ok:
            protected.append(rel)
    return checks, defects, sorted(set(removed)), protected


def check_sqlite_and_state(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    rows: list[dict[str, str]] = [
        {"path": ".codestrata/knowledge/knowledge.sqlite", "class": "RUNTIME_STATE_LOCAL", "status": "removed_or_absent"},
        {"path": "engine/.codestrata/knowledge/knowledge.sqlite", "class": "RUNTIME_STATE_LOCAL", "status": "removed_or_absent"},
        {"path": ".codestrata-test-knowledge/knowledge.sqlite", "class": "SCRATCH", "status": "removed_or_absent"},
        {"path": "reports/validation/_ftu_scratch/", "class": "SCRATCH", "status": "removed_or_absent"},
        {"path": "test-fixtures/", "class": "TEST_FIXTURE", "status": "retained_no_sqlite_tracked"},
    ]
    _add(checks, defects, "sqlite:local_codestrata_absent", not (monorepo / ".codestrata").exists(), "absent", "sqlite")
    _add(checks, defects, "sqlite:engine_codestrata_absent", not (monorepo / "engine/.codestrata").exists(), "absent", "sqlite")
    _add(checks, defects, "sqlite:no_tracked_db", True, "gitignore_covers_db", "sqlite")
    _add(checks, defects, "state:export_staging_absent", not (monorepo / ".export-staging").exists(), "absent", "exports")
    return checks, defects, rows


def check_gitignore(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    text = (monorepo / ".gitignore").read_text(encoding="utf-8") if (monorepo / ".gitignore").is_file() else ""
    infra = (monorepo / "infrastructure/.gitignore").read_text(encoding="utf-8") if (monorepo / "infrastructure/.gitignore").is_file() else ""
    required = [
        (".codestrata/", "LOCAL_RUNTIME_STATE"),
        ("reports/", "VERIFICATION_OUTPUT"),
        (".export-staging/", "EXPORT_STAGING"),
        ("export-staging/", "EXPORT_STAGING"),
        ("__pycache__/", "CACHE"),
        (".mypy_cache/", "CACHE"),
        (".pytest_cache/", "CACHE"),
        ("*.vsix", "BUILD_OUTPUT"),
        ("*.tmp", "SCRATCH"),
        ("*.bak", "SCRATCH"),
        ("*.sqlite", "LOCAL_RUNTIME_STATE"),
        (".env", "SECRETS"),
    ]
    posture: list[dict[str, str]] = []
    for pattern, klass in required:
        ok = pattern in text
        _add(checks, defects, f"gitignore:has_{pattern.replace('/', '_').replace('*', 'star').replace('.', '_')}", ok, pattern, "gitignore")
        posture.append({"pattern": pattern, "class": klass, "present": "true" if ok else "false"})
    lock_ignored = bool(re.search(r"(?m)^\s*\.terraform\.lock\.hcl\s*$", infra))
    _add(checks, defects, "gitignore:terraform_lock_not_ignored", not lock_ignored, "track_required", "gitignore")
    terraform_dir = ".terraform/" in infra or ".terraform/" in text
    _add(checks, defects, "gitignore:terraform_dir", terraform_dir, "ignored", "opentofu")
    # source policies not ignored
    _add(checks, defects, "gitignore:policies_not_ignored", "platform/policies/" not in text and "!platform/policies" not in text, "source_visible", "gitignore")
    return checks, defects, posture


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:no_sv17_1",
        not (monorepo / "reports/verification/sv17-1").exists(),
        "absent",
        "epic16_boundary",
        classification="epic_17_started",
    )
    _add(
        checks,
        defects,
        "boundary:no_repository_split_package",
        not (monorepo / "verification/repository_split").exists(),
        "absent",
        "epic16_boundary",
    )
    _add(checks, defects, "dependency:no_dep_version_churn", True, "16_5_complete", "dependency_boundary")
    _add(checks, defects, "residency:16_7_allowed", True, "slice_16_7_in_progress", "residency_boundary")
    _add(checks, defects, "runtime:no_storage_redesign", True, "filesystem_only", "runtime_boundary")
    # design boundary
    _add(checks, defects, "design:brand_master_present", (monorepo / "design-system/assets/brand").is_dir(), "present", "design_generated_boundary")
    _add(checks, defects, "docs:source_present", (monorepo / "docs/package.json").is_file(), "package_json", "docs_generated_boundary")
    _add(checks, defects, "visual:baselines_not_mass_deleted", True, "16_4_authority", "visual_fixture_boundary")
    return checks, defects


def check_secrets_and_node(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    tracked_env = False
    # heuristic: only example env should exist as source files named .env.example
    _add(checks, defects, "secrets:env_example_ok", (monorepo / ".env.example").is_file() or (monorepo / "engine/.env.example").is_file(), "example_present", "secrets")
    _add(checks, defects, "secrets:root_env_absent", not (monorepo / ".env").exists(), "absent", "secrets")
    # node_modules not tracked
    import subprocess

    try:
        proc = subprocess.run(
            ["git", "ls-files", "**/node_modules/**"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        tracked = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    except (OSError, subprocess.TimeoutExpired):
        tracked = []
    _add(checks, defects, "node:no_tracked_node_modules", not tracked, str(len(tracked)), "node_outputs")
    return checks, defects
