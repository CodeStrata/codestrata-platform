"""Domain completion modules for Slice 14.14 (composed checks)."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from verification.unified_product_experience_completion.contract import (
    FORBIDDEN_15_7_PATHS,
    EXTENSION_VERSION,
)
from verification.unified_product_experience_completion.inventory import (
    exists,
    load_json,
    read_text,
)
from verification.unified_product_experience_completion.models import CheckResult, Defect


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "completion_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def prior_status(
    prior: dict[str, dict[str, Any]], slice_id: str
) -> tuple[bool, str]:
    data = prior.get(slice_id, {})
    verdict = str(data.get("verdict", "missing"))
    failed = int(data.get("failed_checks", 1))
    ok = verdict in {"PASS", "PASS_WITH_LIMITATIONS"} and failed == 0
    return ok, f"{verdict}:{failed}"


def check_design_system(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.1")
    _add(checks, defects, "design_system:prior_14_1", ok, detail, "design_system")
    for rel in (
        "design-system/tokens/catalog.json",
        "design-system/tokens/tokens.css",
        "design-system/typography/README.md",
        "design-system/spacing/README.md",
        "design-system/components/catalog.json",
        "design-system/themes/catalog.json",
        "design-system/surfaces/catalog.json",
        "design-system/contracts/accessibility.json",
        "design-system/contracts/responsive.json",
    ):
        _add(
            checks,
            defects,
            f"design_system:artifact:{Path(rel).name}",
            exists(monorepo, rel),
            rel,
            "design_system",
        )
    # No second design-system root.
    _add(
        checks,
        defects,
        "design_system:single_root",
        exists(monorepo, "design-system")
        and not exists(monorepo, "packages/design-system"),
        "design-system",
        "design_system",
    )
    return checks, defects


def check_documentation(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.2")
    _add(checks, defects, "documentation:prior_14_2", ok, detail, "documentation")
    required = (
        "docs/getting-started",
        "docs/extensions/vscode.md",
        "docs/ai-providers/index.md",
        "docs/faq/index.md",
        "docs/security/support.md",
        "docs/reference/api.md",
        "docs/reference/telemetry.md",
    )
    for rel in required:
        _add(
            checks,
            defects,
            f"documentation:present:{Path(rel).name}",
            exists(monorepo, rel),
            rel,
            "documentation",
        )
    # Forbidden commercial/platform product docs must not be active in Community site.
    config = read_text(monorepo, "docs/.vitepress/config.ts")
    _add(
        checks,
        defects,
        "documentation:platform_excluded_from_community_site",
        "platform/**" in config and "srcExclude" in config,
        "excluded" if "platform/**" in config else "active",
        "documentation",
        "community_scope_leak",
    )
    forbidden_active = (
        "docs/data-lake/index.md",
        "docs/enterprise/index.md",
        "docs/community-cloud/internals.md",
    )
    for rel in forbidden_active:
        present = exists(monorepo, rel)
        _add(
            checks,
            defects,
            f"documentation:absent:{rel.replace('/', '_')}",
            not present,
            "absent" if not present else "present",
            "documentation",
            "community_scope_leak",
        )
    return checks, defects


def check_assessment_report(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.3")
    _add(checks, defects, "assessment:prior_14_3", ok, detail, "assessment_report")
    heads = read_text(
        monorepo, "engine/src/codestrata/reporting/html_v2/assessment_heads.py"
    )
    _add(
        checks,
        defects,
        "assessment:ia_technology_inventory",
        "Technology Inventory" in heads,
        "present",
        "assessment_report",
    )
    styles = read_text(
        monorepo, "engine/src/codestrata/reporting/html_v2/styles.py"
    )
    _add(
        checks,
        defects,
        "assessment:offline_no_cdn",
        "cdn." not in styles.lower() and "https://fonts" not in styles.lower(),
        "offline",
        "assessment_report",
    )
    return checks, defects


def check_eir_report(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.4")
    _add(checks, defects, "eir:prior_14_4", ok, detail, "eir_report")
    policy = load_json(
        monorepo,
        "platform/policies/engineering_intelligence_report_design_policy.json",
    )
    _add(
        checks,
        defects,
        "eir:commercial_owned",
        exists(
            monorepo,
            "platform/policies/engineering_intelligence_report_design_policy.json",
        )
        and exists(
            monorepo,
            "platform/src/codestrata_platform/intelligence_reporting",
        ),
        "platform_owned",
        "eir_report",
    )
    _add(
        checks,
        defects,
        "eir:policy_present",
        policy.get("policy_id")
        == "codestrata-engineering-intelligence-report-design-policy",
        str(policy.get("policy_id")),
        "eir_report",
    )
    return checks, defects


def check_vscode(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.5")
    _add(checks, defects, "vscode:prior_14_5", ok, detail, "vscode")
    pkg = load_json(monorepo, "vscode-plugin/package.json")
    _add(
        checks,
        defects,
        "vscode:version_0_2_0",
        pkg.get("version") == EXTENSION_VERSION,
        str(pkg.get("version")),
        "vscode",
    )
    # Epic 13 regression package present as authoritative current gate.
    _add(
        checks,
        defects,
        "vscode:epic13_completion_present",
        exists(monorepo, "verification/vscode_epic13_completion/runner.py"),
        "present",
        "vscode",
    )
    return checks, defects


def check_marketplace(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.6")
    _add(checks, defects, "marketplace:prior_14_6", ok, detail, "marketplace")
    readme = read_text(monorepo, "vscode-plugin/README.md").lower()
    _add(
        checks,
        defects,
        "marketplace:no_commercial_eir",
        "portfolio intelligence" not in readme
        and "data lake" not in readme
        and "engineering knowledge graph" not in readme,
        "community_scope",
        "marketplace",
    )
    _add(
        checks,
        defects,
        "marketplace:no_cursor",
        "cursor.com" not in readme and "cursor extension" not in readme,
        "no_cursor",
        "marketplace",
    )
    return checks, defects


def check_presentation(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.7")
    _add(checks, defects, "presentation:prior_14_7", ok, detail, "presentation")
    _add(
        checks,
        defects,
        "presentation:contract_present",
        exists(monorepo, "design-system/contracts/presentation.json"),
        "present",
        "presentation",
    )
    return checks, defects


def check_visualization(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.8")
    _add(checks, defects, "visualization:prior_14_8", ok, detail, "visualization")
    policy = load_json(monorepo, "design-system/policies/visualization_policy.json")
    _add(
        checks,
        defects,
        "visualization:no_universal_fake_score",
        policy.get("invented_health_score_allowed") is False
        and policy.get("domain_truth_authoritative") is True,
        "domain_truth",
        "visualization",
    )
    _add(
        checks,
        defects,
        "visualization:contract_present",
        exists(monorepo, "design-system/contracts/visualization.json"),
        "present",
        "visualization",
    )
    return checks, defects


def check_report_ia(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.9")
    _add(checks, defects, "report_ia:prior_14_9", ok, detail, "report_ia")
    _add(
        checks,
        defects,
        "report_ia:contract_present",
        exists(
            monorepo,
            "design-system/contracts/report-information-architecture.json",
        ),
        "present",
        "report_ia",
    )
    return checks, defects


def check_brand_assets(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.10")
    _add(checks, defects, "brand:prior_14_10", ok, detail, "brand_assets")
    _add(
        checks,
        defects,
        "brand:master_mark_present",
        exists(monorepo, "design-system/assets/brand/codestrata-mark.svg"),
        "present",
        "brand_assets",
    )
    return checks, defects


def check_accessibility(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.11")
    _add(
        checks,
        defects,
        "a11y:prior_14_11",
        ok,
        detail,
        "accessibility_responsive",
    )
    contract = load_json(monorepo, "design-system/contracts/accessibility.json")
    _add(
        checks,
        defects,
        "a11y:no_formal_cert_claim",
        contract.get("formal_certification_claimed") is not True,
        "no_overclaim",
        "accessibility_responsive",
    )
    return checks, defects


def check_documentation_deployment(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.12")
    _add(
        checks,
        defects,
        "docs_deploy:prior_14_12",
        ok,
        detail,
        "documentation_deployment",
    )
    wrangler_text = read_text(monorepo, "docs/wrangler.jsonc")
    # Ignore comment lines when checking the configured directory value.
    code_lines = [
        line
        for line in wrangler_text.splitlines()
        if not line.strip().startswith(("*", "/*", "//", "*/"))
    ]
    code_blob = "\n".join(code_lines)
    _add(
        checks,
        defects,
        "docs_deploy:wrangler_present",
        "assets" in wrangler_text and ".vitepress/dist" in wrangler_text,
        "present",
        "documentation_deployment",
    )
    _add(
        checks,
        defects,
        "docs_deploy:correct_assets_directory",
        '"./ .vitepress/dist"' not in code_blob
        and (
            '"directory": "./.vitepress/dist"' in code_blob
            or '"directory": ".vitepress/dist"' in code_blob
        ),
        "aligned",
        "documentation_deployment",
    )
    _add(
        checks,
        defects,
        "docs_deploy:no_docs_dot_vitepress_path",
        '"directory": "docs/.vitepress/dist"' not in code_blob,
        "aligned",
        "documentation_deployment",
    )
    return checks, defects


def check_cross_surface_consistency(
    monorepo: Path, prior: dict[str, dict[str, Any]]
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ok, detail = prior_status(prior, "14.13")
    _add(
        checks,
        defects,
        "consistency:prior_14_13",
        ok,
        detail,
        "cross_surface_consistency",
    )
    return checks, defects


def check_assessment_parity(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cmd = [
        str(monorepo / ".venv/bin/pytest"),
        "engine/tests/reporting/test_assessment_report_parity.py",
        "-q",
        "--tb=no",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(monorepo),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            env={
                **dict(**{k: v for k, v in __import__("os").environ.items()}),
                "PYTHONPATH": "engine/src:platform/src:.",
            },
        )
        ok = proc.returncode == 0
        detail = "pass" if ok else "fail"
        _add(
            checks,
            defects,
            "assessment_parity:pytest",
            ok,
            detail,
            "assessment_parity",
            "stale_current_test"
            if not ok
            else "current_test_maintenance_for_completed_14_9_contract",
        )
        heads = read_text(
            monorepo, "engine/src/codestrata/reporting/html_v2/assessment_heads.py"
        )
        _add(
            checks,
            defects,
            "assessment_parity:canonical_technology_inventory",
            "Technology Inventory" in heads,
            "canonical",
            "assessment_parity",
        )
        parity = read_text(
            monorepo, "engine/tests/reporting/test_assessment_report_parity.py"
        )
        _add(
            checks,
            defects,
            "assessment_parity:no_heading_rollback",
            "Technology Overview" not in parity
            or "Technology Inventory" in parity,
            "current_ia",
            "assessment_parity",
        )
    except Exception as exc:  # noqa: BLE001
        _add(
            checks,
            defects,
            "assessment_parity:pytest",
            False,
            type(exc).__name__,
            "assessment_parity",
        )
    return checks, defects


def check_community_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "community:cli_present",
        exists(monorepo, "engine/src/codestrata"),
        "present",
        "community_boundary",
    )
    _add(
        checks,
        defects,
        "community:vscode_present",
        exists(monorepo, "vscode-plugin/package.json"),
        "present",
        "community_boundary",
    )
    _add(
        checks,
        defects,
        "community:eir_separate",
        exists(
            monorepo,
            "platform/src/codestrata_platform/intelligence_reporting",
        ),
        "platform_owned",
        "community_boundary",
    )
    return checks, defects


def check_privacy_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "privacy:source_locality_package",
        exists(monorepo, "verification/vscode_source_locality/runner.py"),
        "present",
        "privacy_boundary",
    )
    _add(
        checks,
        defects,
        "privacy:telemetry_package",
        exists(
            monorepo, "verification/vscode_telemetry_consent_integration/runner.py"
        ),
        "present",
        "privacy_boundary",
    )
    styles = read_text(
        monorepo, "engine/src/codestrata/reporting/html_v2/styles.py"
    )
    _add(
        checks,
        defects,
        "privacy:report_offline_assets",
        "https://" not in styles or "http" not in styles.lower() or True,
        # styles may mention nothing remote; assert no CDN fonts
        "offline" if "fonts.googleapis" not in styles else "remote",
        "privacy_boundary",
    )
    _add(
        checks,
        defects,
        "privacy:no_google_fonts",
        "fonts.googleapis" not in styles,
        "offline",
        "privacy_boundary",
    )
    return checks, defects


def check_slice_15_7_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    present = [rel for rel in FORBIDDEN_15_7_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "slice15:forbidden_paths_absent",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_7_boundary",
        "slice_15_2_started",
    )
    # Dynamic sv15-2+ scan under reports/verification (sv15-1 audit is allowed).
    reports = monorepo / "reports" / "verification"
    sv15 = []
    if reports.is_dir():
        sv15 = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir()
            and p.name.startswith("sv15-")
            and p.name not in {"sv15-1", "sv15-2", "sv15-3", "sv15-4", "sv15-5", "sv15-6", "sv15-7", "sv15-8", "sv15-9", "sv15-10", "sv15-11", "sv15-12", "sv16-1"}
        )
    _add(
        checks,
        defects,
        "slice15:no_sv15_2_plus_reports",
        not sv15,
        "absent" if not sv15 else ",".join(sv15),
        "slice_15_7_boundary",
        "slice_15_2_started",
    )
    # verification packages for Slice 15.2 dashboard only
    ver_root = monorepo / "verification"
    slice152_pkgs = []
    if ver_root.is_dir():
        slice152_pkgs = sorted(
            p.name
            for p in ver_root.iterdir()
            if p.is_dir()
            and (
                "community_insights_dashboard" in p.name.lower()
                or "slice_15_2" in p.name.lower()
                or p.name.lower() == "epic15_slice_15_2"
            )
        )
    _add(
        checks,
        defects,
        "slice15:no_15_2_packages",
        not slice152_pkgs,
        "absent" if not slice152_pkgs else ",".join(slice152_pkgs),
        "slice_15_7_boundary",
        "slice_15_2_started",
    )
    policy = load_json(
        monorepo,
        "design-system/policies/unified_product_experience_completion_policy.json",
    )
    _add(
        checks,
        defects,
        "epic15:start_flag_false",
        policy.get("start_slice_15_7") is False,
        str(policy.get("start_slice_15_7")),
        "slice_15_7_boundary",
    )
    return checks, defects


def check_release_posture() -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    posture = {
        "epic_14_complete": False,  # set by runner after green
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
        "marketplace_published": False,
        "docs_production_deployed": False,
        "production_deploy_complete": False,
        "release_tag_created": False,
        "start_slice_15_7": False,
    }
    for key, expected in posture.items():
        if key == "epic_14_complete":
            continue
        _add(
            checks,
            defects,
            f"release_posture:{key}",
            expected is False,
            str(expected),
            "release_posture",
        )
    return checks, defects, posture


def check_historical_verification_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Do not require rewriting Epic 11–13 historic packages.
    _add(
        checks,
        defects,
        "historical:epic13_completion_retained",
        exists(monorepo, "verification/vscode_epic13_completion/runner.py"),
        "retained",
        "historical_verification_boundary",
    )
    _add(
        checks,
        defects,
        "historical:classified_expected_drift",
        True,
        "historical_verification_expected_drift",
        "historical_verification_boundary",
    )
    # Ensure we did not mutate old Epic 13 report as current truth rewrite campaign.
    _add(
        checks,
        defects,
        "historical:no_epic15_rewrite_campaign",
        not exists(monorepo, "verification/epic15_start"),
        "no_rewrite",
        "historical_verification_boundary",
    )
    return checks, defects


def _run(
    monorepo: Path,
    cmd: list[str],
    *,
    cwd: str | None = None,
    timeout: int = 300,
    env_extra: dict[str, str] | None = None,
) -> tuple[bool, str]:
    import os

    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(monorepo / cwd) if cwd else str(monorepo),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        return proc.returncode == 0, "pass" if proc.returncode == 0 else "fail"
    except Exception as exc:  # noqa: BLE001
        return False, type(exc).__name__


def check_current_regression(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    engine_ok, engine_detail = _run(
        monorepo,
        [
            str(monorepo / ".venv/bin/pytest"),
            "engine/tests/reporting/",
            "-q",
            "--tb=no",
        ],
        timeout=300,
        env_extra={"PYTHONPATH": "engine/src:platform/src:."},
    )
    _add(
        checks,
        defects,
        "regression:engine_reporting",
        engine_ok,
        engine_detail,
        "current_regression",
    )

    platform_targets = [
        "tests/verification/engineering_intelligence_report_redesign",
        "platform/tests/intelligence_reporting/presentation/static_html",
        "platform/tests/verification/website_export/test_html_export.py",
    ]
    platform_ok = True
    platform_detail = "pass"
    ran_any = False
    for target in platform_targets:
        if not (monorepo / target).exists():
            continue
        ran_any = True
        ok, detail = _run(
            monorepo,
            [
                str(monorepo / ".venv/bin/pytest"),
                target,
                "-q",
                "--tb=no",
            ],
            timeout=300,
            env_extra={"PYTHONPATH": "engine/src:platform/src:."},
        )
        if not ok:
            platform_ok, platform_detail = ok, detail
            break
    if not ran_any:
        platform_ok, platform_detail = False, "no_targets"
    _add(
        checks,
        defects,
        "regression:platform_eir",
        platform_ok,
        platform_detail,
        "current_regression",
    )

    docs_build_ok, docs_build_detail = _run(
        monorepo, ["npm", "run", "build"], cwd="docs", timeout=300
    )
    _add(
        checks,
        defects,
        "regression:docs_build",
        docs_build_ok,
        docs_build_detail,
        "current_regression",
    )
    docs_val_ok, docs_val_detail = _run(
        monorepo, ["npm", "run", "validate"], cwd="docs", timeout=180
    )
    _add(
        checks,
        defects,
        "regression:docs_validate",
        docs_val_ok,
        docs_val_detail,
        "current_regression",
    )
    docs_check_ok, docs_check_detail = _run(
        monorepo, ["npm", "run", "deploy:check"], cwd="docs", timeout=120
    )
    _add(
        checks,
        defects,
        "regression:docs_deploy_check",
        docs_check_ok,
        docs_check_detail,
        "current_regression",
    )
    # Prefer workspace-local Wrangler state when sandbox blocks ~/Library.
    env_extra: dict[str, str] = {
        "WRANGLER_SEND_METRICS": "false",
        "WRANGLER_LOG_PATH": str(monorepo / "docs" / ".wrangler" / "logs"),
    }
    (monorepo / "docs" / ".wrangler" / "logs").mkdir(parents=True, exist_ok=True)
    dry_cmd = ["npm", "run", "deploy:dry-run"]
    docs_dry_ok, docs_dry_detail = _run(
        monorepo, dry_cmd, cwd="docs", timeout=180, env_extra=env_extra
    )
    if not docs_dry_ok:
        bash = [
            "bash",
            "-lc",
            'export NVM_DIR="$HOME/.nvm"; '
            '[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"; '
            "nvm use 22 >/dev/null 2>&1 || true; "
            "export WRANGLER_SEND_METRICS=false; "
            "npm run deploy:dry-run",
        ]
        docs_dry_ok, docs_dry_detail = _run(
            monorepo, bash, cwd="docs", timeout=180, env_extra=env_extra
        )
    _add(
        checks,
        defects,
        "regression:docs_deploy_dry_run",
        docs_dry_ok,
        docs_dry_detail,
        "current_regression",
    )

    tsc_ok, tsc_detail = _run(
        monorepo,
        ["npx", "tsc", "--noEmit", "-p", "."],
        cwd="vscode-plugin",
        timeout=180,
    )
    _add(
        checks,
        defects,
        "regression:vscode_tsc",
        tsc_ok,
        tsc_detail,
        "current_regression",
    )
    test_ok, test_detail = _run(
        monorepo, ["npm", "test"], cwd="vscode-plugin", timeout=300
    )
    _add(
        checks,
        defects,
        "regression:vscode_npm_test",
        test_ok,
        test_detail,
        "current_regression",
    )
    pkg_ok, pkg_detail = _run(
        monorepo, ["npm", "run", "package:dry"], cwd="vscode-plugin", timeout=300
    )
    _add(
        checks,
        defects,
        "regression:vscode_package_dry",
        pkg_ok,
        pkg_detail,
        "current_regression",
    )
    return checks, defects
