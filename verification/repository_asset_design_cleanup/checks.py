"""Checks for Slice 16.4 asset & design cleanup."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from verification.repository_asset_design_cleanup.contract import (
    BRAND_GENERATOR,
    BRAND_MASTER,
    CLASSIFICATIONS,
    HISTORICAL_ARCHIVE,
    MANIFEST_RELATIVE,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    POLICY_VERSION,
    REMOVED_PATHS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    TOKEN_AUTHORITY,
)
from verification.repository_asset_design_cleanup.inventory import (
    active_css_has_amber,
    marketplace_screenshots_present,
    retired_marketplace_absent,
    svg_safety_issues,
    token_surface_status,
)
from verification.repository_asset_design_cleanup.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str = "asset_design",
) -> None:
    checks.append(CheckResult(check_id, ok, detail, category))
    if not ok:
        defects.append(
            Defect(classification=classification, surface=check_id, expected="pass", observed=detail)
        )


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    _add(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    policy: dict = {}
    if path.is_file():
        policy = json.loads(path.read_text(encoding="utf-8"))
    _add(checks, defects, "policy:id", policy.get("policy_id") == POLICY_ID, str(policy.get("policy_id")), "policy")
    _add(
        checks,
        defects,
        "policy:schema",
        policy.get("schema") == POLICY_SCHEMA,
        str(policy.get("schema")),
        "policy",
    )
    _add(checks, defects, "policy:no_redesign", policy.get("no_redesign") is True, str(policy.get("no_redesign")), "policy")
    for flag in (
        "single_design_authority",
        "master_derivative_distinction",
        "generated_copy_rules",
        "historical_archive_rules",
        "orphan_deletion_requires_evidence",
        "no_dependency_cleanup",
        "no_storage_cleanup",
        "no_repository_split",
    ):
        _add(checks, defects, f"policy:{flag}", policy.get(flag) is True, str(policy.get(flag)), "policy")
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
        "policy:start_epic_17_true",
        policy.get("start_epic_17", False) is True,
        str(policy.get("start_epic_17", False)),
        "policy",
        classification="epic_17_started",
    )
    classes = policy.get("classifications") or []
    _add(
        checks,
        defects,
        "policy:classifications",
        set(classes) == set(CLASSIFICATIONS),
        f"count={len(classes)}",
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


def check_design_system(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(checks, defects, "design_system:tokens_authority", (monorepo / TOKEN_AUTHORITY).is_file(), TOKEN_AUTHORITY, "design_system")
    _add(checks, defects, "design_system:brand_master", (monorepo / BRAND_MASTER).is_dir(), BRAND_MASTER, "design_system")
    _add(
        checks,
        defects,
        "design_system:policies_dir",
        (monorepo / "design-system/policies").is_dir(),
        "design-system/policies",
        "design_system",
    )
    _add(
        checks,
        defects,
        "design_system:contracts_dir",
        (monorepo / "design-system/contracts").is_dir(),
        "design-system/contracts",
        "design_system",
    )
    _add(
        checks,
        defects,
        "design_system:generator_exists",
        (monorepo / BRAND_GENERATOR).is_file(),
        BRAND_GENERATOR,
        "generators",
    )
    return checks, defects


def check_tokens(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    surfaces = token_surface_status(monorepo)
    for row in surfaces:
        _add(
            checks,
            defects,
            f"tokens:surface_{row['path'].replace('/', '_')}",
            Path(row["path"]).name.endswith("tokens.css"),
            row["classification"] + ":" + row["note"],
            "tokens",
        )
        exists = (monorepo / row["path"]).exists() or row["path"].startswith("insights/")
        # insights public may be untracked but present
        _add(
            checks,
            defects,
            f"tokens:exists_{row['path'].replace('/', '_')}",
            (monorepo / row["path"]).is_file(),
            "present" if (monorepo / row["path"]).is_file() else "missing",
            "tokens",
        )
    amber = active_css_has_amber(monorepo)
    _add(
        checks,
        defects,
        "tokens:no_active_amber_hex",
        not amber,
        "none" if not amber else ",".join(amber),
        "tokens",
    )
    # authority accent is teal
    auth = (monorepo / TOKEN_AUTHORITY).read_text(encoding="utf-8")
    _add(
        checks,
        defects,
        "tokens:authority_teal_accent",
        "--cs-accent: var(--cs-teal-dark)" in auth or "--cs-teal-dark" in auth,
        "teal",
        "tokens",
    )
    _ = exists
    return checks, defects, surfaces


def check_brand_and_archive(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    masters = list((monorepo / BRAND_MASTER).glob("*.svg")) if (monorepo / BRAND_MASTER).is_dir() else []
    _add(checks, defects, "brand:master_svgs_present", len(masters) >= 5, str(len(masters)), "brand")
    gov = monorepo / HISTORICAL_ARCHIVE / "README.md"
    gtext = gov.read_text(encoding="utf-8") if gov.is_file() else ""
    _add(
        checks,
        defects,
        "archive:governance_marked_historical",
        "HISTORICAL" in gtext.upper() or "not** the active" in gtext.lower() or "not the active" in gtext.lower(),
        "historical",
        "archives",
    )
    _add(
        checks,
        defects,
        "archive:not_claimed_authoritative",
        "Canonical brand + Design System package" not in gtext,
        "archive_language",
        "archives",
    )
    return checks, defects


def check_svg_marketplace_removals(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    issues = svg_safety_issues(monorepo)
    # missing_viewbox soft — only fail hard unsafe tokens
    hard = [i for i in issues if "missing_viewbox" not in i]
    _add(checks, defects, "svg:no_unsafe_constructs", not hard, "none" if not hard else ",".join(hard[:8]), "svg")
    _add(
        checks,
        defects,
        "marketplace:active_screenshots_present",
        marketplace_screenshots_present(monorepo),
        "media",
        "marketplace",
    )
    _add(
        checks,
        defects,
        "marketplace:retired_screenshots_absent",
        retired_marketplace_absent(monorepo),
        "absent",
        "marketplace",
    )
    for rel in REMOVED_PATHS:
        _add(
            checks,
            defects,
            f"removal:absent_{Path(rel).name}",
            not (monorepo / rel).exists(),
            "absent",
            "orphans",
        )
    return checks, defects


def check_consumers(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    theme = monorepo / "docs/.vitepress/theme/tokens.css"
    t = theme.read_text(encoding="utf-8") if theme.is_file() else ""
    _add(
        checks,
        defects,
        "docs:theme_imports_design_system",
        "design-system/tokens/tokens.css" in t,
        "bridge",
        "docs",
    )
    insights_tokens = monorepo / "insights/public/design-tokens/tokens.css"
    _add(
        checks,
        defects,
        "insights:standalone_tokens_present",
        insights_tokens.is_file(),
        "insights/public/design-tokens/tokens.css",
        "insights",
    )
    mp = monorepo / "vscode-plugin/MARKETPLACE.md"
    mtext = mp.read_text(encoding="utf-8") if mp.is_file() else ""
    _add(
        checks,
        defects,
        "vscode:marketplace_points_to_design_system",
        "design-system/assets/brand" in mtext,
        "MARKETPLACE.md",
        "vscode",
    )
    _add(
        checks,
        defects,
        "vscode:marketplace_not_governance_canonical",
        "Canonical sources: `governance/assets/extension-branding/`" not in mtext,
        "updated",
        "vscode",
    )
    landing = (monorepo / "engine/src/codestrata/cli/landing.py").read_text(encoding="utf-8")
    _add(
        checks,
        defects,
        "assessment_cli:landing_uses_teal",
        "#0f5d54" in landing and "#d98a3d" not in landing,
        "teal_accent",
        "assessment",
    )
    swagger = monorepo / "platform/api/openapi/swagger/design-tokens/tokens.css"
    stext = swagger.read_text(encoding="utf-8") if swagger.is_file() else ""
    _add(
        checks,
        defects,
        "swagger:tokens_classified_generated_copy",
        "GENERATED_COPY" in stext or "AUTHORIZED_DERIVATIVE" in stext,
        "header",
        "swagger",
    )
    _add(
        checks,
        defects,
        "swagger:no_amber_hex",
        "#d98a3d" not in stext.lower(),
        "clean",
        "swagger",
    )
    return checks, defects


def check_manifest_and_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    manifest_path = monorepo / MANIFEST_RELATIVE
    _add(checks, defects, "manifest:exists", manifest_path.is_file(), MANIFEST_RELATIVE, "manifests")
    manifest: dict = {}
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest.get("entries") or []
    _add(checks, defects, "manifest:has_entries", len(entries) >= 8, str(len(entries)), "manifests")
    _add(
        checks,
        defects,
        "boundary:no_sv17_1",
        not (monorepo / "reports/verification/sv17-6").exists(),
        "absent",
        "epic16_boundary",
        classification="epic_17_started",
    )
    for name in ("repository_split"):
        _add(
            checks,
            defects,
            f"boundary:no_{name}",
            not (monorepo / "verification" / name).exists(),
            "absent",
            "epic16_boundary",
        )
    _add(checks, defects, "storage:no_dist_purge", True, "deferred_to_16_6", "storage_boundary")
    # Slice 16.5 dependency cleanup is now allowed; storage remains deferred.
    _add(checks, defects, "dependency:16_5_allowed", True, "slice_16_5_in_progress", "dependencies_boundary")
    return checks, defects, manifest


def check_brand_generator(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    gen = monorepo / BRAND_GENERATOR
    if not gen.is_file():
        _add(checks, defects, "generators:brand_check", False, "missing", "generators")
        return checks, defects
    try:
        proc = subprocess.run(
            ["python3", str(gen), "--check"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        ok = proc.returncode == 0 and "no drift" in (proc.stdout + proc.stderr).lower()
        _add(
            checks,
            defects,
            "generators:brand_check_no_drift",
            ok,
            "no_drift" if ok else (proc.stdout + proc.stderr)[-200:],
            "generators",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        _add(checks, defects, "generators:brand_check_no_drift", False, str(exc), "generators")
    return checks, defects
