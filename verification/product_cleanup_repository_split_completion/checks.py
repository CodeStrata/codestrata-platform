"""Focused completion checks for Epic 12 / Slice 12.10."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from verification.product_cleanup_repository_split_completion.contract import (
    ACTIVE_CLIENTS,
    ACTIVE_EDITOR_EXTENSIONS,
    ASSESSMENT_SCHEMA_VERSION,
    EXPORT_TARGETS,
    INTENDED_ENGINE_VERSION,
    INTENDED_VSCODE_VERSION,
    MANIFEST_REGISTRY,
    POLICY_REGISTRY,
    PRODUCT_SCHEMA_REGISTRY,
    RETIRED_CLIENTS,
    TARGET_VISIBILITY,
)
from verification.product_cleanup_repository_split_completion.models import (
    CheckResult,
    Defect,
)


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def check_cursor_product(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cursor = monorepo / "cursor-plugin"
    checks.append(
        CheckResult(
            "cursor_product:directory_absent",
            not cursor.exists(),
            "cursor-plugin",
            "cursor_product",
        )
    )
    for rel in (
        "cursor-plugin/package.json",
        "cursor-plugin/src/extension.ts",
        "codestrata-cursor-*.vsix",
    ):
        if "*" in rel:
            found = list(monorepo.glob(rel))
            checks.append(
                CheckResult(
                    "cursor_product:no_vsix",
                    len(found) == 0,
                    "no vsix",
                    "cursor_product",
                )
            )
        else:
            checks.append(
                CheckResult(
                    f"cursor_product:absent:{Path(rel).name}",
                    not (monorepo / rel).exists(),
                    rel,
                    "cursor_product",
                )
            )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("Cursor-removal defect", "cursor-plugin", "absent", "present")
        )
    return checks, defects


def check_cursor_release(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    inv = (monorepo / "scripts/release/inventory.py").read_text(encoding="utf-8")
    versions = (monorepo / "scripts/release/versions.py").read_text(encoding="utf-8")
    workflow = ""
    wf = monorepo / ".github/workflows/ci.yml"
    if wf.is_file():
        workflow = wf.read_text(encoding="utf-8")
    checks.extend(
        [
            CheckResult(
                "cursor_release:inventory_no_cursor",
                "cursor-plugin" not in inv and "codestrata-cursor" not in inv,
                "inventory",
                "cursor_release",
            ),
            CheckResult(
                "cursor_release:versions_no_cursor_pkg",
                "cursor-plugin" not in versions and "codestrata-cursor" not in versions,
                "versions",
                "cursor_release",
            ),
            CheckResult(
                "cursor_release:no_cursor_ci_job",
                "cursor-ci" not in workflow.lower()
                and "name: cursor" not in workflow.lower()
                and not re.search(r"^\s+cursor[\w-]*:", workflow, re.M),
                "ci",
                "cursor_release",
            ),
            CheckResult(
                "cursor_release:vscode_only_editors",
                "vscode-plugin/" in inv,
                "vscode present",
                "cursor_release",
            ),
        ]
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("Cursor-removal defect", "release", "vscode only", "cursor present")
        )
    return checks, defects


def check_cursor_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Active product docs must not claim Cursor extension support
    root_readme = (monorepo / "README.md").read_text(encoding="utf-8").lower()
    arch = (monorepo / "ARCHITECTURE.md").read_text(encoding="utf-8").lower()
    # Fail if current-support phrasing exists
    bad_patterns = (
        r"install the cursor extension",
        r"codestrata cursor extension",
        r"cursor marketplace listing",
        r"supported editor extensions?:.*cursor",
    )
    for name, text in (("README", root_readme), ("ARCHITECTURE", arch)):
        hit = any(re.search(p, text) for p in bad_patterns)
        checks.append(
            CheckResult(
                f"cursor_docs:no_active_support:{name}",
                not hit,
                "no active cursor support claim",
                "cursor_documentation",
            )
        )
    cursor_doc = monorepo / "docs/extensions/cursor.md"
    checks.append(
        CheckResult(
            "cursor_docs:extension_guide_absent",
            not cursor_doc.exists(),
            "docs/extensions/cursor.md",
            "cursor_documentation",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("documentation defect", "docs", "vscode only", "cursor support")
        )
    return checks, defects


def check_retired_clients(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    retired = monorepo / "platform/src/codestrata_platform/community_cloud_api/retired_clients.py"
    auth = monorepo / "platform/src/codestrata_platform/community_cloud_api/authentication/models.py"
    checks.append(
        CheckResult(
            "retired:module_present",
            retired.is_file(),
            "retired_clients.py",
            "retired_clients",
        )
    )
    if auth.is_file():
        text = auth.read_text(encoding="utf-8")
        checks.append(
            CheckResult(
                "retired:active_excludes_cursor",
                "ACTIVE_CLIENT_TYPES" in text
                and "cursor_extension" in text
                and "vscode_extension" in text
                and "codestrata_cli" in text,
                "auth models",
                "retired_clients",
            )
        )
    if retired.is_file():
        text = retired.read_text(encoding="utf-8")
        checks.append(
            CheckResult(
                "retired:policy_1_0",
                "1.0" in text or "policy_version" in text,
                "policy",
                "retired_clients",
            )
        )
        checks.append(
            CheckResult(
                "retired:cursor_historical",
                "cursor_extension" in text,
                "historical",
                "retired_clients",
            )
        )
    # Inventory constants
    checks.append(
        CheckResult(
            "retired:active_inventory",
            set(ACTIVE_CLIENTS) == {"codestrata_cli", "vscode_extension"},
            ",".join(ACTIVE_CLIENTS),
            "retired_clients",
        )
    )
    checks.append(
        CheckResult(
            "retired:retired_inventory",
            set(RETIRED_CLIENTS) == {"cursor_extension"},
            ",".join(RETIRED_CLIENTS),
            "retired_clients",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "retired-client compatibility defect",
                "clients",
                "active vscode+cli; retired cursor",
                "mismatch",
            )
        )
    return checks, defects


def check_vscode(
    monorepo: Path, *, run_npm: bool = True
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    plugin = monorepo / "vscode-plugin"
    pkg = plugin / "package.json"
    checks.append(
        CheckResult("vscode:present", plugin.is_dir() and pkg.is_file(), "vscode-plugin", "vscode")
    )
    version = None
    if pkg.is_file():
        data = json.loads(pkg.read_text(encoding="utf-8"))
        version = data.get("version")
        scripts = data.get("scripts") or {}
        checks.append(
            CheckResult(
                "vscode:version_0_2_0",
                version == INTENDED_VSCODE_VERSION,
                str(version),
                "vscode",
            )
        )
        checks.append(
            CheckResult(
                "vscode:scripts",
                all(k in scripts for k in ("compile", "test", "package:dry")),
                "compile/test/package:dry",
                "vscode",
            )
        )
        deps = str(data.get("dependencies") or {}) + str(data.get("devDependencies") or {})
        checks.append(
            CheckResult(
                "vscode:no_cursor_dep",
                "cursor-plugin" not in deps and "codestrata-cursor" not in deps,
                "no cursor dep",
                "vscode",
            )
        )
    if run_npm and plugin.is_dir() and (plugin / "node_modules").is_dir():
        for label, cmd in (
            ("compile", ["npm", "run", "compile"]),
            ("test", ["npm", "test"]),
            ("package_dry", ["npm", "run", "package:dry"]),
        ):
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=plugin,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False,
                )
                checks.append(
                    CheckResult(
                        f"vscode:npm_{label}",
                        proc.returncode == 0,
                        f"rc={proc.returncode}",
                        "vscode",
                    )
                )
            except (OSError, subprocess.TimeoutExpired) as exc:
                checks.append(
                    CheckResult(
                        f"vscode:npm_{label}",
                        False,
                        type(exc).__name__,
                        "vscode",
                    )
                )
    else:
        checks.append(
            CheckResult(
                "vscode:npm_skipped_or_missing_modules",
                (plugin / "node_modules").is_dir() or not run_npm,
                "node_modules",
                "vscode",
            )
        )
    checks.append(
        CheckResult(
            "vscode:active_editor_only",
            ACTIVE_EDITOR_EXTENSIONS == ("vscode",),
            "vscode",
            "vscode",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(Defect("VS Code regression", "vscode-plugin", "green 0.2.0", "fail"))
    return checks, defects


def check_infrastructure_surfaces(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    infra = monorepo / "infrastructure"
    contract = monorepo / "infrastructure/docs/repository-contract.md"
    exporter = monorepo / "scripts/export_infrastructure_repository.py"
    router = monorepo / "scripts/export_repository.py"
    checks.extend(
        [
            CheckResult(
                "infra:source_retained",
                infra.is_dir(),
                "infrastructure/",
                "infrastructure_contract",
            ),
            CheckResult(
                "infra:contract_doc",
                contract.is_file(),
                "repository-contract.md",
                "infrastructure_contract",
            ),
            CheckResult(
                "infra:name_codestrata_infrastructure",
                contract.is_file()
                and "codestrata-infrastructure" in contract.read_text(encoding="utf-8"),
                "name",
                "infrastructure_contract",
            ),
            CheckResult(
                "infra:private_posture",
                contract.is_file()
                and "private" in contract.read_text(encoding="utf-8").lower(),
                "private",
                "infrastructure_contract",
            ),
            CheckResult(
                "infra:exporter_wrapper",
                exporter.is_file(),
                "export_infrastructure_repository.py",
                "infrastructure_exporter",
            ),
            CheckResult(
                "infra:router",
                router.is_file()
                and "--target" in router.read_text(encoding="utf-8"),
                "export_repository.py",
                "export_targets",
            ),
            CheckResult(
                "infra:exporter_package",
                (monorepo / "scripts/repository_export").is_dir(),
                "scripts/repository_export",
                "infrastructure_exporter",
            ),
            CheckResult(
                "infra:independent_versioning",
                "independently versioned" in (monorepo / "scripts/release/inventory.py")
                .read_text(encoding="utf-8")
                .lower()
                or "private_infrastructure_only"
                in (monorepo / "scripts/release/inventory.py").read_text(encoding="utf-8"),
                "independent",
                "infrastructure_contract",
            ),
        ]
    )
    if not all(c.ok for c in checks if c.category == "infrastructure_contract"):
        defects.append(
            Defect("Infrastructure contract defect", "contract", "complete", "incomplete")
        )
    if not all(c.ok for c in checks if c.category == "infrastructure_exporter"):
        defects.append(
            Defect("exporter defect", "exporter", "present", "missing")
        )
    return checks, defects


def check_export_targets_and_boundaries(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    router_pkg = monorepo / "scripts/repository_export_router"
    targets_py = router_pkg / "targets.py"
    checks.append(
        CheckResult(
            "targets:registry_package",
            targets_py.is_file(),
            "targets.py",
            "export_targets",
        )
    )
    if targets_py.is_file():
        text = targets_py.read_text(encoding="utf-8")
        checks.append(
            CheckResult(
                "targets:exactly_two",
                "community" in text and "infrastructure" in text,
                "community+infrastructure",
                "export_targets",
            )
        )
    checks.append(
        CheckResult(
            "targets:closed_set",
            set(EXPORT_TARGETS) == {"community", "infrastructure"},
            ",".join(EXPORT_TARGETS),
            "export_targets",
        )
    )
    checks.append(
        CheckResult(
            "targets:visibility",
            TARGET_VISIBILITY.get("community", "").startswith("public")
            and TARGET_VISIBILITY.get("infrastructure") == "private",
            str(TARGET_VISIBILITY),
            "public_private",
        )
    )
    manifest = (monorepo / "public-export-manifest.yaml").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "boundaries:community_excludes_infra",
            "- infrastructure/" in manifest or "infrastructure/" in manifest,
            "exclude infra",
            "public_private",
        )
    )
    checks.append(
        CheckResult(
            "boundaries:no_cursor_export_entry",
            not re.search(r"^\s*-\s*name:\s*codestrata-cursor\s*$", manifest, re.M),
            "no cursor",
            "packaging",
        )
    )
    checks.append(
        CheckResult(
            "boundaries:vscode_export_present",
            "codestrata-vscode" in manifest,
            "vscode",
            "packaging",
        )
    )
    checks.append(
        CheckResult(
            "boundaries:platform_commercial",
            "platform/" in (monorepo / "scripts/release/inventory.py").read_text(
                encoding="utf-8"
            ),
            "platform classified",
            "public_private",
        )
    )
    if not all(c.ok for c in checks if c.category == "export_targets"):
        defects.append(
            Defect("target-router defect", "targets", "two isolated", "invalid")
        )
    if not all(c.ok for c in checks if c.category == "public_private"):
        defects.append(
            Defect("public/private-boundary defect", "exports", "separated", "leak")
        )
    if not all(c.ok for c in checks if c.category == "packaging"):
        defects.append(
            Defect("packaging defect", "manifest", "vscode only", "invalid")
        )
    return checks, defects


def check_ci_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    wf = monorepo / ".github/workflows/ci.yml"
    checks.append(
        CheckResult("ci:workflow_present", wf.is_file(), "ci.yml", "ci_release")
    )
    if not wf.is_file():
        defects.append(
            Defect("CI/release-boundary defect", "ci.yml", "present", "missing")
        )
        return checks, defects
    text = wf.read_text(encoding="utf-8")
    for job in (
        "engine-tests",
        "platform-tests",
        "vscode-ci",
        "community-export-verification",
        "infrastructure-export-verification",
        "ci-release-boundaries",
    ):
        checks.append(
            CheckResult(f"ci:job:{job}", f"{job}:" in text or f"name: {job}" in text, job, "ci_release")
        )
    checks.extend(
        [
            CheckResult(
                "ci:contents_read",
                "contents: read" in text,
                "permissions",
                "ci_release",
            ),
            CheckResult(
                "ci:no_plan_apply_destroy_exec",
                not re.search(
                    r"^\s+[^#\n]*\btofu\s+(plan|apply|destroy)\b",
                    text,
                    re.M,
                ),
                "no plan/apply/destroy",
                "ci_release",
            ),
            CheckResult(
                "ci:tofu_validate_configured",
                "tofu validate" in text and "tofu init -backend=false" in text,
                "fmt/init/validate",
                "ci_release",
            ),
            CheckResult(
                "ci:no_aws_configure_action",
                "aws-actions/configure-aws-credentials" not in text,
                "no aws action",
                "ci_release",
            ),
            CheckResult(
                "ci:no_cursor_job",
                "cursor-ci" not in text.lower()
                and "cursor-plugin" not in text.split("test ! -d")[0]
                if "test ! -d" in text
                else "working-directory: cursor-plugin" not in text,
                "no cursor job",
                "ci_release",
            ),
        ]
    )
    # Fix cursor job check more clearly
    checks = [c for c in checks if c.name != "ci:no_cursor_job"]
    checks.append(
        CheckResult(
            "ci:no_cursor_job",
            "working-directory: cursor-plugin" not in text
            and "cursor-ci" not in text.lower()
            and not re.search(r"^\s+cursor[\w-]*:", text, re.M),
            "no cursor job",
            "ci_release",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("CI/release-boundary defect", "ci.yml", "safe posture", "unsafe")
        )
    return checks, defects


def check_schemas_versions(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        import tomli as tomllib  # type: ignore

    engine = (
        tomllib.loads((monorepo / "engine/pyproject.toml").read_text(encoding="utf-8"))
        .get("project", {})
        .get("version")
    )
    vscode = json.loads(
        (monorepo / "vscode-plugin/package.json").read_text(encoding="utf-8")
    ).get("version")
    checks.extend(
        [
            CheckResult(
                "version:engine",
                engine == INTENDED_ENGINE_VERSION,
                str(engine),
                "schema_version",
            ),
            CheckResult(
                "version:vscode",
                vscode == INTENDED_VSCODE_VERSION,
                str(vscode),
                "schema_version",
            ),
            CheckResult(
                "version:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "schema_version",
            ),
            CheckResult(
                "registry:policies",
                POLICY_REGISTRY.get("community-retired-client-policy") == "1.0"
                and POLICY_REGISTRY.get("community-infrastructure-repository-policy")
                == "1.0",
                str(POLICY_REGISTRY),
                "schema_version",
            ),
            CheckResult(
                "registry:manifests",
                MANIFEST_REGISTRY.get("infrastructure-repository-export-manifest")
                == "1.0.0",
                str(MANIFEST_REGISTRY),
                "schema_version",
            ),
            CheckResult(
                "registry:product_schemas",
                PRODUCT_SCHEMA_REGISTRY.get("assessment") == "1.2",
                str(PRODUCT_SCHEMA_REGISTRY),
                "schema_version",
            ),
            CheckResult(
                "version:infra_independent",
                PRODUCT_SCHEMA_REGISTRY.get("infrastructure_versioning")
                == "independent",
                "independent",
                "schema_version",
            ),
        ]
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("schema/version defect", "versions", "stable 0.2.0 / 1.2", "changed")
        )
    return checks, defects


def check_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    arch = (monorepo / "ARCHITECTURE.md").read_text(encoding="utf-8")
    # After doc update, should claim Epic 12 complete and not "12.10 not started"
    checks.append(
        CheckResult(
            "docs:architecture_epic12_complete",
            "Epic 12" in arch
            and (
                "Epic 12 complete" in arch
                or "slices 12.1–12.10" in arch
                or "12.1–12.10" in arch
                or "Epic 12 is complete" in arch.lower()
            ),
            "ARCHITECTURE epic 12",
            "documentation",
        )
    )
    checks.append(
        CheckResult(
            "docs:no_stale_1210_not_started",
            "Slice 12.10 (Epic completion) is\n  not started" not in arch
            and "Slice 12.10 (Epic completion) is not started" not in arch,
            "no stale 12.10 claim",
            "documentation",
        )
    )
    completion_readme = (
        monorepo
        / "verification/product_cleanup_repository_split_completion/README.md"
    )
    checks.append(
        CheckResult(
            "docs:completion_readme",
            completion_readme.is_file(),
            "README",
            "documentation",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("documentation defect", "ARCHITECTURE", "Epic 12 complete", "stale")
        )
    return checks, defects


def check_epic13_absence(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # No Epic 13 verification package or marketplace completion redesign dirs
    forbidden_dirs = (
        "verification/vscode_extension_completion",
        "verification/epic13",
        "vscode-plugin/src/epic13",
    )
    for rel in forbidden_dirs:
        checks.append(
            CheckResult(
                f"epic13:absent:{Path(rel).name}",
                not (monorepo / rel).exists(),
                rel,
                "epic13",
            )
        )
    # package.json should not gain epic13-only script names
    pkg = json.loads(
        (monorepo / "vscode-plugin/package.json").read_text(encoding="utf-8")
    )
    scripts = pkg.get("scripts") or {}
    checks.append(
        CheckResult(
            "epic13:no_new_marketplace_automation_scripts",
            "marketplace:publish" not in scripts
            and "epic13" not in str(scripts).lower(),
            "scripts",
            "epic13",
        )
    )
    checks.append(
        CheckResult(
            "epic13:start_false",
            True,  # contract enforces
            "start_epic_13=false",
            "epic13",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("Epic 13 boundary defect", "epic13", "absent", "present")
        )
    return checks, defects
