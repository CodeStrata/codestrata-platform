"""Version registry consistency."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from verification.repository_consistency.contract import VERSION_ANCHORS
from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_versions(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    registry: dict[str, str] = {}

    # Engine
    eng = monorepo / "engine/pyproject.toml"
    if eng.is_file():
        data = tomllib.loads(eng.read_text(encoding="utf-8"))
        ver = data.get("project", {}).get("version", "")
        registry["engine_cli"] = ver
        add_check(
            checks,
            defects,
            "versions:engine_0_2_0",
            ver == VERSION_ANCHORS["engine_cli"],
            ver,
            "versions",
            classification="version_conflict",
        )

    # VS Code
    vs = monorepo / "vscode-plugin/package.json"
    if vs.is_file():
        data = json.loads(vs.read_text(encoding="utf-8"))
        ver = str(data.get("version", ""))
        registry["vscode"] = ver
        add_check(
            checks,
            defects,
            "versions:vscode_0_2_0",
            ver == VERSION_ANCHORS["vscode"],
            ver,
            "versions",
            classification="version_conflict",
        )

    # Assessment schema 1.2 — authoritative constant + schema tree
    found_12 = False
    const_path = monorepo / "engine/src/codestrata/reporting/contract/constants.py"
    if const_path.is_file():
        ct = const_path.read_text(encoding="utf-8")
        if re.search(r'ASSESSMENT_JSON_SCHEMA_VERSION\s*=\s*"1\.2"', ct):
            found_12 = True
    schema_dir = monorepo / "engine/src/codestrata/resources/schemas/assessment/codestrata.io/v1.2"
    schema_file = schema_dir / "AssessmentReport.json"
    if schema_file.is_file():
        st = schema_file.read_text(encoding="utf-8")
        if '"const": "1.2"' in st or '"const":"1.2"' in st:
            found_12 = True
    registry["assessment"] = "1.2" if found_12 else "unknown"
    add_check(
        checks,
        defects,
        "versions:assessment_1_2",
        found_12,
        registry["assessment"],
        "versions",
        classification="version_conflict",
    )

    # Epic 16 verification schemas 1.0.0
    for pkg in (
        "repository_inventory",
        "repository_documentation",
        "repository_code_cleanup",
        "repository_asset_design_cleanup",
        "repository_dependency_build_cleanup",
        "repository_storage_generated_cleanup",
        "repository_boundary_residency",
        "repository_consistency",
    ):
        cp = monorepo / f"verification/{pkg}/contract.py"
        if cp.is_file():
            t = cp.read_text(encoding="utf-8")
            m = re.search(r'SCHEMA_VERSION\s*=\s*"([^"]+)"', t)
            ver = m.group(1) if m else ""
            registry[f"epic16_{pkg}"] = ver
            add_check(
                checks,
                defects,
                f"versions:epic16_{pkg}",
                ver == "1.0.0",
                ver,
                "versions",
            )

    # Insights policies 1.0 family
    insights_pol = monorepo / "platform/policies/codestrata_insights_dashboard_policy.json"
    if insights_pol.is_file():
        data = json.loads(insights_pol.read_text(encoding="utf-8"))
        ver = str(data.get("policy_version") or data.get("schema") or "")
        registry["insights_dashboard_policy"] = ver
        add_check(
            checks,
            defects,
            "versions:insights_policy_1_0_family",
            "1.0" in ver,
            ver,
            "versions",
        )

    # No conflicting hardcoded engine versions in README
    readme = monorepo / "README.md"
    if readme.is_file():
        t = readme.read_text(encoding="utf-8")
        bad = re.findall(r"(?i)engine(?:/cli)?\s+(?:version\s+)?(\d+\.\d+\.\d+)", t)
        conflicts = [v for v in bad if v != "0.2.0"]
        add_check(
            checks,
            defects,
            "versions:readme_engine_coherent",
            not conflicts,
            ",".join(conflicts) or "0.2.0",
            "versions",
        )

    return checks, defects, registry
