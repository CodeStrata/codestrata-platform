"""Checks for Slice 18.6 — Public Surface Reconciliation."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from verification.community_public_surface_reconciliation.contract import (
    ASSESS_PY,
    CLAIM_REGISTER_RELATIVE,
    CLI_DOC,
    CLI_INIT,
    COMMUNITY_CLOUD_DOC,
    CONTRADICTION_REGISTER_RELATIVE,
    ENGINE_PRIVACY,
    ENGINE_README,
    ENGINE_SECURITY,
    FORBIDDEN_18_7_PACKAGES,
    LANDING_PY,
    PACKAGE_INIT,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    PYPROJECT,
    ROOT_SECURITY,
    STALE_PUBLIC_PATTERNS,
    VSCODE_DOC,
    VSCODE_README,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_public_surface_reconciliation.helpers import (
    add_check,
    load_json,
    read_text,
)
from verification.community_public_surface_reconciliation.models import CheckResult, Defect

CANONICAL_DOMAINS = (
    "https://docs.codestrata.ai",
    "https://api.codestrata.ai",
    "https://reports.codestrata.ai",
)
PRIVACY_URLS = (
    "https://docs.codestrata.ai/security/privacy",
    "https://docs.codestrata.ai/security/data-collection",
    "https://docs.codestrata.ai/security/source-locality",
    "https://docs.codestrata.ai/security/retention-and-deletion",
)


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / POLICY_RELATIVE
    policy = load_json(path) if path.is_file() else {}
    add_check(checks, defects, "policy:present", path.is_file(), POLICY_RELATIVE, "policy")
    for key, expected in sorted(POLICY_REQUIRED_VALUES.items()):
        add_check(
            checks,
            defects,
            f"policy:{key}",
            policy.get(key) == expected,
            f"{key}={policy.get(key)!r}",
            "policy",
        )
    return checks, defects, policy


def check_version_truth(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    init_text = read_text(monorepo / PACKAGE_INIT)
    pyproject = read_text(monorepo / PYPROJECT)
    add_check(
        checks,
        defects,
        "version:package_init_0_2_0",
        '__version__ = "0.2.0"' in init_text,
        "codestrata.__version__",
        "version",
    )
    add_check(
        checks,
        defects,
        "version:pyproject_0_2_0",
        'version = "0.2.0"' in pyproject,
        "engine/pyproject.toml",
        "version",
    )
    import os

    proc = subprocess.run(
        [
            str(monorepo / ".venv/bin/python"),
            "-c",
            "from codestrata.package_metadata import get_package_version, format_version_line; "
            "print(get_package_version()); print(format_version_line())",
        ],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": f"{monorepo / 'engine' / 'src'}:{monorepo / 'platform' / 'src'}:{monorepo}",
        },
    )
    out = (proc.stdout or "").strip().splitlines()
    pkg_ver = out[0] if out else ""
    line = out[1] if len(out) > 1 else ""
    add_check(
        checks,
        defects,
        "version:runtime_reports_0_2_0",
        pkg_ver == "0.2.0" and "0.2.0" in line,
        f"pkg={pkg_ver!r} line={line!r}",
        "version",
    )
    limitations.append("github_release_still_0_1_0")
    return checks, defects, limitations


def check_cli_surfaces(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    texts: dict[str, str] = {}
    required = {
        "landing": LANDING_PY,
        "cli_init": CLI_INIT,
        "assess": ASSESS_PY,
        "engine_readme": ENGINE_README,
        "engine_security": ENGINE_SECURITY,
        "engine_privacy": ENGINE_PRIVACY,
        "root_security": ROOT_SECURITY,
        "cli_doc": CLI_DOC,
        "vscode_doc": VSCODE_DOC,
        "community_cloud": COMMUNITY_CLOUD_DOC,
        "vscode_readme": VSCODE_README,
    }
    for key, rel in required.items():
        path = monorepo / rel
        text = read_text(path)
        texts[key] = text
        add_check(
            checks,
            defects,
            f"docs:present:{key}",
            path.is_file() and len(text) > 100,
            rel,
            "docs",
        )
    landing = texts.get("landing", "")
    cli_init = texts.get("cli_init", "")
    assess = texts.get("assess", "")
    add_check(
        checks,
        defects,
        "cli:bare_no_output_reports",
        "--output reports" not in landing,
        "landing Start Here",
        "bare_cli",
    )
    add_check(
        checks,
        defects,
        "cli:bare_assess_canonical",
        "codestrata assess --repo ." in landing,
        "canonical assess",
        "bare_cli",
    )
    add_check(
        checks,
        defects,
        "cli:bare_engineering_assessment",
        "Engineering Assessment" in landing,
        "product category",
        "terminology",
    )
    add_check(
        checks,
        defects,
        "cli:bare_not_engineering_intelligence",
        "Engineering Intelligence" not in landing,
        "no EI label on welcome",
        "terminology",
    )
    add_check(
        checks,
        defects,
        "cli:bare_telemetry_discovery",
        "Disabled by default" in landing
        and "--telemetry-allow" in landing
        and "--telemetry-deny" in landing,
        "telemetry discovery",
        "bare_cli",
    )
    add_check(
        checks,
        defects,
        "cli:bare_contrast_palette",
        "LandingPalette" in landing
        and "bright_yellow" in landing
        and "bright_cyan" in landing
        and "bright_white" in landing
        and '="#0f5d54"' not in landing.replace(" ", "")
        and "='#0f5d54'" not in landing.replace(" ", "")
        and '="#16756a"' not in landing.replace(" ", "")
        and "='#16756a'" not in landing.replace(" ", "")
        and "bgcolor=" not in landing
        and "rgb(" not in landing.lower(),
        "ANSI high-contrast palette",
        "contrast",
    )
    add_check(
        checks,
        defects,
        "cli:bare_publish_discovery",
        "Reports are local by default" in landing
        and "report publish" in landing
        and "r/<opaque-id>" in landing,
        "publish discovery",
        "bare_cli",
    )
    add_check(
        checks,
        defects,
        "cli:bare_engine_version_meta",
        "Engine " in landing and "Community Edition" in landing,
        "version meta",
        "bare_cli",
    )
    add_check(
        checks,
        defects,
        "cli:help_no_output_reports",
        "--output reports" not in cli_init,
        "root help",
        "cli_help",
    )
    add_check(
        checks,
        defects,
        "cli:help_telemetry",
        "--telemetry-allow" in cli_init and "report publish" in cli_init,
        "help discovery",
        "cli_help",
    )
    add_check(
        checks,
        defects,
        "cli:assess_doc_canonical",
        "codestrata assess --repo . --no-ai" in assess
        and assess.count("--output reports") == 0,
        "assess help/doc",
        "cli_help",
    )
    add_check(
        checks,
        defects,
        "cli:artifact_detector",
        ".codestrata-artifacts/assessments" in landing,
        "start-here detector",
        "artifact_path",
    )
    return checks, defects, texts


def check_readme_security_privacy(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    readme = texts.get("engine_readme", "")
    add_check(
        checks,
        defects,
        "readme:artifact_layout",
        ".codestrata-artifacts/assessments" in readme and "assessment.html" in readme,
        "artifact layout",
        "readme",
    )
    add_check(
        checks,
        defects,
        "readme:no_legacy_dated_tree",
        "YYYYMMDD-HHMMSS" not in readme and "reports/<repository-name>" not in readme,
        "no stale tree",
        "readme",
    )
    add_check(
        checks,
        defects,
        "readme:telemetry_publish",
        "--telemetry-allow" in readme and "report publish" in readme,
        "telemetry+publish",
        "readme",
    )
    add_check(
        checks,
        defects,
        "readme:no_stale_output_reports",
        "--output reports" not in readme,
        "no --output reports",
        "readme",
    )
    sec = texts.get("engine_security", "") + "\n" + texts.get("root_security", "")
    add_check(
        checks,
        defects,
        "security:0_2_supported",
        "0.2.x" in sec,
        "supported versions",
        "security",
    )
    add_check(
        checks,
        defects,
        "security:privacy_links",
        all(u in sec or u in texts.get("engine_privacy", "") for u in PRIVACY_URLS[:2]),
        "privacy discovery",
        "security",
    )
    priv = texts.get("engine_privacy", "")
    add_check(
        checks,
        defects,
        "privacy:canonical_docs",
        all(u in priv for u in PRIVACY_URLS),
        "engine PRIVACY canonical",
        "privacy",
    )
    return checks, defects


def check_docs_and_vscode(
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    cli = texts.get("cli_doc", "")
    vs = texts.get("vscode_doc", "")
    cloud = texts.get("community_cloud", "")
    vs_readme = texts.get("vscode_readme", "")
    add_check(
        checks,
        defects,
        "docs_cli:version_semantics",
        "Installed package/runtime" in cli or "installed package" in cli.lower(),
        "version semantics",
        "docs_cli",
    )
    add_check(
        checks,
        defects,
        "docs_cli:examples",
        "--telemetry-allow" in cli and "reports.codestrata.ai/r/" in cli,
        "examples",
        "docs_cli",
    )
    add_check(
        checks,
        defects,
        "docs_cli:no_output_reports",
        "--output reports" not in cli,
        "no stale path",
        "docs_cli",
    )
    add_check(
        checks,
        defects,
        "docs_vscode:candidate_vsix",
        "candidate VSIX" in vs or "Marketplace" in vs,
        "marketplace honesty",
        "docs_vscode",
    )
    add_check(
        checks,
        defects,
        "docs_vscode:publish_command",
        "Publish" in vs and "confirm-public-publish" in vs,
        "publish",
        "docs_vscode",
    )
    add_check(
        checks,
        defects,
        "docs_vscode:assessment_html",
        "assessment.html" in vs,
        "artifact path",
        "docs_vscode",
    )
    add_check(
        checks,
        defects,
        "status:version_semantics",
        "Installed CLI" in cloud and "published" in cloud.lower(),
        "status semantics",
        "community_status",
    )
    add_check(
        checks,
        defects,
        "vscode_readme:marketplace_not_live",
        "Marketplace" in vs_readme
        and ("not** complete" in vs_readme or "not complete" in vs_readme.lower() or "VSIX" in vs_readme),
        "marketplace",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "vscode_readme:publish_command",
        "Publish/Share" in vs_readme and "assessment.html" in vs_readme,
        "commands",
        "vscode",
    )
    add_check(
        checks,
        defects,
        "terminology:vscode_display_assessment",
        "CodeStrata – Engineering Assessment" in vs_readme,
        "vscode product name",
        "terminology",
    )
    add_check(
        checks,
        defects,
        "domains:canonical",
        all(d in (cli + cloud + vs) for d in CANONICAL_DOMAINS),
        "canonical domains",
        "domains",
    )
    add_check(
        checks,
        defects,
        "domains:no_execute_api_authority",
        not re.search(
            r"[a-z0-9]+\.execute-api\.[a-z0-9-]+\.amazonaws\.com",
            cli + cloud + vs + texts.get("engine_readme", ""),
        ),
        "no execute-api",
        "domains",
    )
    limitations.append("marketplace_content_not_published")
    limitations.append("website_favicon_deferred")
    limitations.append("openai_owner_credential_required")
    limitations.append("openrouter_owner_credential_required")
    return checks, defects, limitations


def check_terminology(
    monorepo: Path,
    texts: dict[str, str],
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    term_reg = load_json(
        monorepo / "platform/policies/community_product_terminology_register.json"
    )
    add_check(
        checks,
        defects,
        "terminology:register_present",
        term_reg.get("register_id") == "community-product-terminology-register",
        "terminology register",
        "terminology",
    )
    terms = term_reg.get("terms") if isinstance(term_reg.get("terms"), dict) else {}
    ea = terms.get("engineering_assessment") if isinstance(terms.get("engineering_assessment"), dict) else {}
    ei = terms.get("engineering_intelligence") if isinstance(terms.get("engineering_intelligence"), dict) else {}
    add_check(
        checks,
        defects,
        "terminology:assessment_scope",
        ea.get("scope") == "single_repository" and ea.get("output") == "assessment_report",
        str(ea),
        "terminology",
    )
    add_check(
        checks,
        defects,
        "terminology:intelligence_scope",
        ei.get("scope") == "portfolio_multi_repository"
        and ei.get("output") == "engineering_intelligence_report",
        str(ei),
        "terminology",
    )
    getting = read_text(monorepo / "docs/getting-started/index.md")
    assessments = read_text(monorepo / "docs/assessments/index.md")
    eir_docs = read_text(monorepo / "docs/reports/engineering-intelligence.md")
    if not eir_docs:
        eir_docs = read_text(monorepo / "docs/ai-providers/index.md")
    add_check(
        checks,
        defects,
        "terminology:getting_started_model",
        "single-repository" in getting.lower() or "Single-repository" in getting,
        "product model",
        "terminology",
    )
    add_check(
        checks,
        defects,
        "terminology:assessments_not_ei_default",
        "Deterministic Engineering Assessment" in assessments
        and "Deterministic Engineering Intelligence" not in assessments,
        "assessments page",
        "terminology",
    )
    add_check(
        checks,
        defects,
        "terminology:eir_retained",
        "Engineering Intelligence" in eir_docs
        and (
            "Engineering Intelligence Report" in eir_docs
            or "EIR" in eir_docs
        ),
        "EIR docs retained",
        "terminology",
    )
    pkg = load_json(monorepo / "vscode-plugin/package.json")
    add_check(
        checks,
        defects,
        "terminology:vscode_package_display",
        pkg.get("displayName") == "CodeStrata – Engineering Assessment",
        str(pkg.get("displayName")),
        "terminology",
    )
    landing = texts.get("landing", "")
    add_check(
        checks,
        defects,
        "terminology:landing_not_ei",
        "Engineering Intelligence" not in landing and "Engineering Assessment" in landing,
        "landing terminology",
        "terminology",
    )
    return checks, defects


def check_stale_strings(texts: dict[str, str]) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    public_blob = "\n".join(
        [
            texts.get("landing", ""),
            texts.get("cli_init", ""),
            texts.get("engine_readme", ""),
            texts.get("cli_doc", ""),
            texts.get("vscode_doc", ""),
            texts.get("vscode_readme", ""),
        ]
    )
    for pattern in STALE_PUBLIC_PATTERNS:
        add_check(
            checks,
            defects,
            f"stale:absent_{re.sub(r'[^a-z0-9]+', '_', pattern.lower())[:40]}",
            pattern not in public_blob,
            pattern,
            "stale_strings",
        )
    return checks, defects


def check_claims(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, Any]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    claims_reg = load_json(monorepo / CLAIM_REGISTER_RELATIVE)
    entries = claims_reg.get("entries") if isinstance(claims_reg.get("entries"), list) else []
    add_check(
        checks,
        defects,
        "claims:register_present",
        len(entries) >= 10,
        f"count={len(entries)}",
        "claims",
    )
    summarized: list[dict[str, Any]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        claim_id = str(e.get("claim_id") or "")
        doc_rel = str(e.get("public_document") or "")
        doc_text = read_text(monorepo / doc_rel) if doc_rel else ""
        ok = bool(
            claim_id
            and doc_rel
            and doc_text
            and e.get("register_18_1")
            and e.get("runtime_evidence")
            and e.get("validation_status") == "PASS"
        )
        add_check(checks, defects, f"claims:{claim_id or 'unknown'}", ok, doc_rel, "claims")
        summarized.append(
            {
                "claim_id": claim_id,
                "public_document": doc_rel,
                "validation_status": e.get("validation_status"),
                "ok": ok,
            }
        )
    return checks, defects, summarized


def check_contradictions(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = load_json(monorepo / CONTRADICTION_REGISTER_RELATIVE)
    entries = reg.get("entries") if isinstance(reg.get("entries"), list) else []
    by_id = {
        str(e.get("contradiction_id")): e
        for e in entries
        if isinstance(e, dict) and e.get("contradiction_id")
    }
    c002 = by_id.get("T18-C002", {})
    c003 = by_id.get("T18-C003", {})
    add_check(
        checks,
        defects,
        "contradiction:T18-C002_expected_gap",
        str(c002.get("classification") or "") == "EXPECTED_RELEASE_GAP",
        str(c002.get("classification")),
        "contradictions",
    )
    add_check(
        checks,
        defects,
        "contradiction:T18-C002_not_resolved",
        str(c002.get("classification") or "") != "RESOLVED",
        "still open until GitHub release",
        "contradictions",
    )
    add_check(
        checks,
        defects,
        "contradiction:T18-C003_carried",
        str(c003.get("classification") or "") != "RESOLVED",
        "favicon deferred",
        "contradictions",
    )
    return checks, defects


def check_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    wf = load_json(monorepo / WORKFLOW_REGISTER_RELATIVE)
    add_check(
        checks,
        defects,
        "boundary:start_18_6",
        wf.get("start_slice_18_6") is True,
        str(wf.get("start_slice_18_6")),
        "boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_18_7_recorded",
        wf.get("start_slice_18_7") in (True, False),
        str(wf.get("start_slice_18_7")),
        "boundary",
        soft=True,
    )
    for pkg in FORBIDDEN_18_7_PACKAGES:
        add_check(
            checks,
            defects,
            f"boundary:absent_{Path(pkg).name}",
            not (monorepo / pkg).exists(),
            pkg,
            "boundary",
        )
    limitations.append("monorepo_pre_cutover_authority")
    limitations.append("full_release_corpus_deferred")
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(monorepo),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.stdout.strip():
        limitations.append("worktree_uncommitted")
    return checks, defects, limitations
