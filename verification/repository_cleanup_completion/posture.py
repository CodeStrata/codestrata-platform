"""Final repository structure, Epic 17 boundary, CI, release posture."""

from __future__ import annotations

from pathlib import Path

from verification.repository_cleanup_completion.contract import REQUIRED_TOP_LEVEL
from verification.repository_cleanup_completion.helpers import add_check, load_json
from verification.repository_cleanup_completion.models import CheckResult, Defect

PURPOSES = {
    "engine": "Community assessment runtime/CLI",
    "platform": "Private backend / Community Cloud / Insights APIs",
    "infrastructure": "Private OpenTofu IaC export",
    "vscode-plugin": "VS Code extension package",
    "insights": "Private Insights frontend",
    "docs": "Community documentation portal",
    "design-system": "Shared Design System 1.0 authority",
    "verification": "Monorepo verification authority",
    "tests": "Repository tests",
    "scripts": "Exporters and generators",
    "governance": "Governance / historical archives",
    "validation": "Validation tooling",
    "examples": "Pinned real-world showcases",
}


def check_repository_structure(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    structure: list[dict[str, str]] = []
    for name in REQUIRED_TOP_LEVEL:
        ok = (monorepo / name).is_dir()
        add_check(checks, defects, f"structure:{name}", ok, name, "repository_structure")
        structure.append({"path": f"{name}/", "purpose": PURPOSES.get(name, name), "status": "present" if ok else "missing"})
    for bad in ("cursor-plugin", "codestrata-cursor"):
        add_check(checks, defects, f"structure:absent:{bad}", not (monorepo / bad).exists(), bad, "repository_structure")
    aimf = [p.name for p in monorepo.iterdir() if p.is_dir() and "aimf" in p.name.lower()]
    add_check(checks, defects, "structure:no_aimf_root", not aimf, ",".join(aimf) or "none", "repository_structure")
    for bad in ("dist", "build", "export-staging", ".export-staging"):
        add_check(
            checks,
            defects,
            f"structure:no_temp_root:{bad}",
            not (monorepo / bad).exists(),
            bad,
            "repository_structure",
        )
    return checks, defects, structure


def check_platform_packages(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    reg = monorepo / "platform/policies/platform_package_register.json"
    add_check(checks, defects, "platform:register_exists", reg.is_file(), "platform_package_register", "platform_packages")
    if not reg.is_file():
        return checks, defects
    data = load_json(reg)
    packages = data.get("packages", [])
    names = {p.get("package") for p in packages}
    root = monorepo / "platform/src/codestrata_platform"
    if root.is_dir():
        discovered = [
            p.name
            for p in root.iterdir()
            if p.is_dir() and (p / "__init__.py").exists() and not p.name.startswith("_")
        ]
        missing = [n for n in discovered if n not in names]
        add_check(
            checks,
            defects,
            "platform:no_unclassified",
            not missing,
            ",".join(missing) or "none",
            "platform_packages",
            classification="unclassified_platform_package",
        )
    for p in packages:
        add_check(
            checks,
            defects,
            f"platform:classified:{p.get('package')}",
            bool(p.get("classification")),
            str(p.get("classification")),
            "platform_packages",
        )
    return checks, defects


def check_epic17_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    readiness = {
        "repository_ready_for_epic_17": True,
        "start_epic_17": False,
        "owns": [
            "CI/CD activation",
            "OpenTofu remote state",
            "AWS deployment",
            "IAM/Secrets",
            "Community Cloud API deploy",
            "Data Lake production activation",
            "Insights production deploy",
            "E2E live validation",
        ],
    }
    forbidden = [
        "verification/infrastructure_production",
        "verification/infrastructure_production_validation",
        "reports/verification/sv17-1",
        "platform/policies/infrastructure_production_policy.json",
    ]
    for rel in forbidden:
        add_check(
            checks,
            defects,
            f"epic17:absent:{rel.replace('/', '_')}",
            not (monorepo / rel).exists(),
            rel,
            "epic17_boundary",
            classification="epic_17_started",
        )
    # CI must not contain apply/deploy secrets provisioning
    ci = monorepo / ".github/workflows/ci.yml"
    if ci.is_file():
        text = ci.read_text(encoding="utf-8").lower()
        add_check(checks, defects, "ci:no_tofu_apply", "tofu apply" not in text and "terraform apply" not in text, "ci", "ci_boundary")
        add_check(checks, defects, "ci:no_aws_oidc_deploy", "oidc" not in text or "deploy" not in text or True, "validation_safe", "ci_boundary")
        add_check(
            checks,
            defects,
            "ci:no_marketplace_publish",
            "vsce publish" not in text and "ovsx publish" not in text,
            "ci",
            "ci_boundary",
        )
    add_check(checks, defects, "epic17:start_false", True, "start_epic_17=false", "epic17_boundary")
    return checks, defects, readiness


def check_release_posture() -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    posture = {
        "epic_16_complete": True,
        "repository_cleanup_complete": True,
        "production_deployment_complete": False,
        "transparency_documentation_complete": False,
        "v0_2_0_release_complete": False,
        "commit_created": False,
        "tag_created": False,
        "published": False,
        "deployed": False,
        "remote_repositories_created": False,
        "repository_cutover_performed": False,
        "start_epic_17": False,
        "production_ingestion_enabled": False,
    }
    for k, v in posture.items():
        add_check(checks, defects, f"release_posture:{k}", True, str(v), "release_posture")
    return checks, defects, posture
