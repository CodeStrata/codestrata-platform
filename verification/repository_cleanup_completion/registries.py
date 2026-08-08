"""Policy / contract / version registries for completion."""

from __future__ import annotations

import json
import re
import tomllib
from collections import defaultdict
from pathlib import Path

from verification.repository_cleanup_completion.contract import VERSION_ANCHORS
from verification.repository_cleanup_completion.helpers import add_check, load_json
from verification.repository_cleanup_completion.models import CheckResult, Defect

AUTHORITATIVE_POLICIES = (
    "repository_cleanup_policy.json",
    "repository_documentation_policy.json",
    "repository_code_cleanup_policy.json",
    "repository_asset_design_cleanup_policy.json",
    "repository_dependency_build_cleanup_policy.json",
    "repository_storage_generated_cleanup_policy.json",
    "repository_boundary_residency_policy.json",
    "repository_consistency_policy.json",
    "repository_package_release_validation_policy.json",
    "repository_cleanup_completion_policy.json",
)


def check_policy_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: list[dict[str, str]] = []
    auth = monorepo / "platform/policies"
    for name in AUTHORITATIVE_POLICIES:
        path = auth / name
        add_check(checks, defects, f"policy_registry:present:{name}", path.is_file(), name, "policy_registry")
        if path.is_file():
            data = load_json(path)
            summary.append(
                {
                    "path": f"platform/policies/{name}",
                    "schema": str(data.get("schema") or ""),
                    "role": "authoritative",
                }
            )
            mirror = monorepo / "insights/policies" / name
            if mirror.is_file():
                identical = mirror.read_bytes() == path.read_bytes()
                add_check(
                    checks,
                    defects,
                    f"policy_registry:mirror:{name}",
                    identical,
                    "byte_identical",
                    "policy_registry",
                    classification="competing_policy_authority",
                )
                summary.append(
                    {
                        "path": f"insights/policies/{name}",
                        "schema": str(data.get("schema") or ""),
                        "role": "consumer_mirror",
                    }
                )
    return checks, defects, summary


def check_contract_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: list[dict[str, str]] = []
    by_schema: dict[str, list[str]] = defaultdict(list)
    for path in sorted((monorepo / "platform/policies").glob("*contract*.json")):
        data = load_json(path)
        schema = str(data.get("schema") or path.stem)
        rel = path.relative_to(monorepo).as_posix()
        by_schema[schema].append(rel)
        summary.append({"path": rel, "identity": schema, "role": "authoritative"})
    for path in sorted((monorepo / "platform/contracts").glob("*.json")):
        data = load_json(path)
        schema = str(data.get("schema") or path.stem)
        rel = path.relative_to(monorepo).as_posix()
        by_schema[schema].append(rel)
        summary.append({"path": rel, "identity": schema, "role": "authoritative"})
    for schema, paths in by_schema.items():
        plat = [p for p in paths if p.startswith("platform/")]
        add_check(
            checks,
            defects,
            f"contract_registry:unique:{schema}",
            len(plat) <= 1 or len(set(plat)) == len(plat),
            ",".join(plat),
            "contract_registry",
            classification="competing_contract_authority",
        )
    return checks, defects, summary


def check_version_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    registry: dict[str, str] = {}
    eng = monorepo / "engine/pyproject.toml"
    if eng.is_file():
        ver = tomllib.loads(eng.read_text(encoding="utf-8")).get("project", {}).get("version", "")
        registry["engine_cli"] = ver
        add_check(checks, defects, "versions:engine", ver == VERSION_ANCHORS["engine_cli"], ver, "version_registry")
    vs = monorepo / "vscode-plugin/package.json"
    if vs.is_file():
        ver = str(json.loads(vs.read_text(encoding="utf-8")).get("version", ""))
        registry["vscode"] = ver
        add_check(checks, defects, "versions:vscode", ver == VERSION_ANCHORS["vscode"], ver, "version_registry")
    const = monorepo / "engine/src/codestrata/reporting/contract/constants.py"
    found = False
    if const.is_file():
        found = bool(re.search(r'ASSESSMENT_JSON_SCHEMA_VERSION\s*=\s*"1\.2"', const.read_text(encoding="utf-8")))
    registry["assessment"] = "1.2" if found else "unknown"
    add_check(checks, defects, "versions:assessment", found, registry["assessment"], "version_registry")
    registry["design_system"] = "1.0"
    add_check(
        checks,
        defects,
        "versions:design_system_root",
        (monorepo / "design-system").is_dir(),
        "design-system/",
        "version_registry",
    )
    return checks, defects, registry
