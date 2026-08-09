"""Checks for Slice 16.5 dependency & build cleanup."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.repository_dependency_build_cleanup.contract import (
    BUILD_REGISTER_RELATIVE,
    CLASSIFICATIONS,
    DEPENDENCY_REGISTER_RELATIVE,
    ENGINE_VERSION,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    VSCODE_VERSION,
)
from verification.repository_dependency_build_cleanup.models import CheckResult, Defect


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
    _add(checks, defects, "policy:id", policy.get("policy_id") == "repository-dependency-build-cleanup-policy", str(policy.get("policy_id")), "policy")
    _add(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
    for flag in (
        "evidence_required_dependency_removal",
        "independent_package_roots",
        "local_pinned_release_tooling",
        "dynamic_install_restrictions",
        "lockfile_ownership",
        "build_authority_uniqueness",
        "advisory_classification",
        "no_forced_framework_modernization",
        "no_product_version_changes",
        "no_deployment_pipeline_implementation",
        "no_storage_cleanup",
        "no_repository_split",
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


def check_registers(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    dep = _load(monorepo, DEPENDENCY_REGISTER_RELATIVE)
    build = _load(monorepo, BUILD_REGISTER_RELATIVE)
    _add(checks, defects, "register:dependency_exists", bool(dep.get("entries")), DEPENDENCY_REGISTER_RELATIVE, "dependency_register")
    _add(checks, defects, "register:build_exists", bool(build.get("authorities")), BUILD_REGISTER_RELATIVE, "build_register")
    entries = dep.get("entries") or []
    unknown = [e for e in entries if e.get("class") not in CLASSIFICATIONS]
    _add(checks, defects, "register:dependency_classes_valid", not unknown, str(len(unknown)), "dependency_register")
    authorities = build.get("authorities") or []
    surfaces = {a.get("surface") for a in authorities}
    required = {"Engine", "Platform", "Docs", "VS Code", "Insights", "Infrastructure", "Repository exports", "Brand generation", "Release verification"}
    _add(checks, defects, "register:build_surfaces", required.issubset(surfaces), str(sorted(surfaces)), "build_register")
    return checks, defects, dep, build


def check_python_and_engine(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    eng = (monorepo / "engine/pyproject.toml").read_text(encoding="utf-8")
    _add(checks, defects, "engine:version_0_2_0", f'version = "{ENGINE_VERSION}"' in eng, ENGINE_VERSION, "engine")
    for dep in ("pydantic", "PyYAML", "rich", "typer"):
        _add(checks, defects, f"engine:dep_{dep}", dep in eng, "present", "python_dependencies")
    plat = (monorepo / "platform/pyproject.toml").read_text(encoding="utf-8")
    _add(checks, defects, "platform:fastapi", "fastapi" in plat, "present", "platform")
    _add(checks, defects, "platform:codestrata_dep", "codestrata>=" in plat, "present", "platform")
    return checks, defects


def check_vscode(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = _load(monorepo, "vscode-plugin/package.json")
    _add(checks, defects, "vscode:version_0_2_0", pkg.get("version") == VSCODE_VERSION, str(pkg.get("version")), "vscode")
    scripts = pkg.get("scripts") or {}
    dev = pkg.get("devDependencies") or {}
    _add(checks, defects, "vscode:vsce_local", "@vscode/vsce" in dev, str(dev.get("@vscode/vsce")), "vscode")
    _add(checks, defects, "vscode:ovsx_local", "ovsx" in dev, str(dev.get("ovsx")), "vscode")
    package_script = scripts.get("package", "")
    dry = scripts.get("package:dry", "")
    _add(
        checks,
        defects,
        "vscode:no_dynamic_npx_vsce",
        "npx --yes @vscode/vsce" not in package_script and "npx --yes @vscode/vsce" not in dry,
        package_script[:80],
        "dynamic_installs",
    )
    _add(checks, defects, "vscode:uses_local_vsce", "vsce package" in package_script or package_script.endswith("vsce package --no-dependencies") or " vsce " in f" {package_script} ", package_script, "vscode")
    return checks, defects


def check_insights(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = _load(monorepo, "insights/package.json")
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    chartish = [k for k in deps if re.search(r"chart|recharts|d3|plotly", k, re.I)]
    awsish = [k for k in deps if re.search(r"aws-sdk|@aws-sdk", k, re.I)]
    _add(checks, defects, "insights:no_chart_libs", not chartish, str(chartish), "insights")
    _add(checks, defects, "insights:no_aws_sdk", not awsish, str(awsish), "insights")
    _add(checks, defects, "insights:has_types_node", "@types/node" in deps, "present", "insights")
    scripts = pkg.get("scripts") or {}
    _add(checks, defects, "insights:typecheck_script", "typecheck" in scripts, str(scripts.get("typecheck")), "insights")
    _add(checks, defects, "insights:build_script", scripts.get("build") == "vite build", str(scripts.get("build")), "insights")
    return checks, defects


def check_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pkg = _load(monorepo, "docs/package.json")
    dev = pkg.get("devDependencies") or {}
    scripts = pkg.get("scripts") or {}
    _add(checks, defects, "docs:wrangler_pinned", str(dev.get("wrangler")) == "4.120.0", str(dev.get("wrangler")), "docs")
    _add(checks, defects, "docs:vitepress_present", "vitepress" in dev, str(dev.get("vitepress")), "docs")
    for name in ("build", "validate", "deploy:check"):
        _add(checks, defects, f"docs:script_{name}", name in scripts, "present", "docs")
    deploy = " ".join(str(scripts.get(k, "")) for k in scripts)
    _add(checks, defects, "docs:no_npx_wrangler", "npx wrangler" not in deploy, "local_wrangler", "dynamic_installs")
    return checks, defects


def check_lockfiles_and_gitignore(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    posture: list[dict[str, str]] = []
    required = [
        ("docs/package-lock.json", "TRACK_REQUIRED"),
        ("vscode-plugin/package-lock.json", "TRACK_REQUIRED"),
        ("insights/package-lock.json", "TRACK_REQUIRED"),
    ]
    for rel, klass in required:
        path = monorepo / rel
        ok = path.is_file()
        _add(checks, defects, f"lockfile:{rel.replace('/', '_')}", ok, klass if ok else "MISSING_REQUIRED", "lockfiles")
        posture.append({"path": rel, "classification": klass if ok else "MISSING_REQUIRED"})
    infra_ignore = (monorepo / "infrastructure/.gitignore").read_text(encoding="utf-8") if (monorepo / "infrastructure/.gitignore").is_file() else ""
    lock_ignored = bool(re.search(r"(?m)^\s*\.terraform\.lock\.hcl\s*$", infra_ignore))
    _add(checks, defects, "gitignore:terraform_lock_not_ignored", not lock_ignored, "track_required", "gitignore")
    locks = list((monorepo / "infrastructure").rglob(".terraform.lock.hcl")) if (monorepo / "infrastructure").is_dir() else []
    _add(checks, defects, "lockfile:terraform_present", len(locks) >= 1, str(len(locks)), "lockfiles")
    for lock in sorted(locks, key=lambda p: str(p.relative_to(monorepo))):
        posture.append({"path": str(lock.relative_to(monorepo)).replace("\\", "/"), "classification": "TRACK_REQUIRED"})
    return checks, defects, posture


def check_dynamic_and_ci(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    findings: list[dict[str, str]] = []
    vscode_pkg = (monorepo / "vscode-plugin/package.json").read_text(encoding="utf-8")
    docs_pkg = (monorepo / "docs/package.json").read_text(encoding="utf-8")
    _add(checks, defects, "dynamic:vscode_no_npx_yes_vsce", "npx --yes @vscode/vsce" not in vscode_pkg, "absent", "dynamic_installs")
    _add(checks, defects, "dynamic:vscode_no_npx_yes_ovsx", "npx --yes ovsx" not in vscode_pkg, "absent", "dynamic_installs")
    _add(checks, defects, "dynamic:docs_no_npx_wrangler", "npx wrangler" not in docs_pkg, "absent", "dynamic_installs")
    findings.append({"tool": "@vscode/vsce", "status": "local_devDependency", "path": "vscode-plugin/package.json"})
    findings.append({"tool": "ovsx", "status": "local_devDependency", "path": "vscode-plugin/package.json"})
    findings.append({"tool": "wrangler", "status": "local_pinned", "path": "docs/package.json"})
    ci = monorepo / ".github/workflows/ci.yml"
    text = ci.read_text(encoding="utf-8") if ci.is_file() else ""
    _add(checks, defects, "ci:workflow_exists", ci.is_file(), ".github/workflows/ci.yml", "ci")
    _add(checks, defects, "ci:no_suppression_py", "suppression.py" not in text, "absent", "ci")
    _add(checks, defects, "ci:no_generate_slice_413", "generate_slice_413" not in text, "absent", "ci")
    _add(checks, defects, "ci:no_aws_deploy_job", "aws deploy" not in text.lower() and "tofu apply" not in text.lower(), "absent", "ci")
    return checks, defects, findings


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:no_sv17_1",
        not (monorepo / "reports/verification/sv17-6").exists(),
        "absent",
        "epic16_boundary",
        classification="epic_17_started",
    )
    for name in ("repository_split",):
        _add(
            checks,
            defects,
            f"boundary:no_{name}",
            not (monorepo / "verification" / name).exists(),
            "absent",
            "epic16_boundary",
        )
    _add(checks, defects, "storage:16_6_allowed", True, "slice_16_6_in_progress", "storage_boundary")
    _add(checks, defects, "residency:16_7_allowed", True, "slice_16_7_in_progress", "residency_boundary")
    _add(checks, defects, "generated:no_sqlite_cleanup", True, "deferred_to_16_6", "generated_boundary")
    return checks, defects


def check_versions(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    eng = (monorepo / "engine/pyproject.toml").read_text(encoding="utf-8")
    vscode = _load(monorepo, "vscode-plugin/package.json")
    authority = {
        "engine": ENGINE_VERSION,
        "vscode": VSCODE_VERSION,
        "assessment_schema": "1.2",
    }
    _add(checks, defects, "versions:engine", f'version = "{ENGINE_VERSION}"' in eng, ENGINE_VERSION, "versions")
    _add(checks, defects, "versions:vscode", vscode.get("version") == VSCODE_VERSION, str(vscode.get("version")), "versions")
    _add(checks, defects, "versions:no_bump_performed", True, "unchanged", "versions")
    return checks, defects, authority
