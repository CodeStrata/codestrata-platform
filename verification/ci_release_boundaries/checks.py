"""Focused boundary checks for Slice 12.9 CI/release surfaces."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.ci_release_boundaries.contract import (
    ACTIVE_EDITOR_EXTENSIONS,
    ALLOWED_LIMITATIONS,
    ASSESSMENT_SCHEMA_VERSION,
    AUTHORITATIVE_EXPORT_COMMAND,
    INTENDED_ENGINE_VERSION,
    INTENDED_VSCODE_VERSION,
    REQUIRED_CI_JOBS,
    SUPPORTED_EXPORT_TARGETS,
)
from verification.ci_release_boundaries.models import CheckResult, Defect
from verification.ci_release_boundaries.workflow_inventory import WorkflowInventory

_PLAN_APPLY_DESTROY = re.compile(
    r"\btofu\s+(plan|apply|destroy)\b|\bterraform\s+(plan|apply|destroy)\b",
    re.IGNORECASE,
)
_GIT_MUTATION = re.compile(
    r"\bgit\s+(init|commit|push|tag|remote\s+add)\b",
    re.IGNORECASE,
)
_AWS_CRED_CONFIG = re.compile(
    r"configure-aws-credentials|AWS_ACCESS_KEY_ID:\s*\$\{\{|id-token:\s*write",
    re.IGNORECASE,
)
_PUBLISH = re.compile(
    r"\b(vsce\s+publish|npm\s+publish|twine\s+upload|gh\s+release\s+create|"
    r"docker\s+push|marketplace\.publish)\b",
    re.IGNORECASE,
)


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def check_cursor_absence(
    inv: WorkflowInventory | None, monorepo: Path
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    jobs = inv.job_names if inv else []
    text = inv.workflow_text if inv else ""
    lower = text.lower()

    # Active Cursor CI jobs must not exist (negative asserts of absence are allowed).
    job_hit = any(
        "cursor" in n.lower() and "absence" not in n.lower() for n in jobs
    )
    checks.append(
        CheckResult(
            "cursor_absent:no_cursor_job",
            not job_hit,
            ",".join(jobs),
            "cursor_absence",
        )
    )
    checks.append(
        CheckResult(
            "cursor_absent:no_cursor_ci_package_job",
            "cursor-ci" not in lower
            and "cursor-package" not in lower
            and "cursor-vsix" not in lower
            and "name: cursor" not in lower,
            "no active cursor jobs",
            "cursor_absence",
        )
    )
    # No Cursor build/test/package steps (allow "codestrata-cursor" only in absence asserts)
    active_cursor_build = bool(
        re.search(
            r"(npm\s+(ci|test|run).*cursor|cursor-plugin\s|/cursor-plugin/|"
            r"working-directory:\s*cursor-plugin)",
            text,
            re.IGNORECASE,
        )
    )
    checks.append(
        CheckResult(
            "cursor_absent:no_build_test_package",
            not active_cursor_build,
            "no cursor build steps",
            "cursor_absence",
        )
    )
    cursor_dir = monorepo / "cursor-plugin"
    checks.append(
        CheckResult(
            "cursor_absent:source_tree",
            not cursor_dir.exists(),
            "cursor-plugin removed",
            "cursor_absence",
        )
    )
    inv_py = (monorepo / "scripts/release/inventory.py").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "cursor_absent:release_inventory",
            "cursor-plugin" not in inv_py and "codestrata-cursor" not in inv_py,
            "inventory",
            "cursor_absence",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("Cursor-removal defect", "ci/release", "absent", "present")
        )
    return checks, defects


def check_vscode_ci(
    inv: WorkflowInventory | None, monorepo: Path
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    body = (inv.job_bodies.get("vscode-ci", "") if inv else "").lower()
    pkg = monorepo / "vscode-plugin" / "package.json"
    version = None
    if pkg.is_file():
        version = json.loads(pkg.read_text(encoding="utf-8")).get("version")
    required_bits = ("npm ci", "npm run compile", "npm test", "package:dry")
    for bit in required_bits:
        checks.append(
            CheckResult(
                f"vscode_ci:{bit.replace(' ', '_')}",
                bit in body,
                bit,
                "vscode_ci",
            )
        )
    checks.append(
        CheckResult(
            "vscode_ci:version_0_2_0",
            version == INTENDED_VSCODE_VERSION,
            str(version),
            "vscode_ci",
        )
    )
    checks.append(
        CheckResult(
            "vscode_ci:no_marketplace_publish",
            "vsce publish" not in body and "npx vsce publish" not in body,
            "no publish command",
            "vscode_ci",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect("VS Code CI regression", "vscode-ci", "complete", "incomplete")
        )
    return checks, defects


def check_community_export_ci(
    inv: WorkflowInventory | None,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    body = inv.job_bodies.get("community-export-verification", "") if inv else ""
    lower = body.lower()
    checks.extend(
        [
            CheckResult(
                "community_export:job_present",
                inv is not None and "community-export-verification" in inv.job_names,
                "job",
                "community_export_ci",
            ),
            CheckResult(
                "community_export:uses_router",
                AUTHORITATIVE_EXPORT_COMMAND in body and "--target community" in body,
                "export_repository.py",
                "community_export_ci",
            ),
            CheckResult(
                "community_export:dry_run_first",
                "--dry-run" in body,
                "dry-run",
                "community_export_ci",
            ),
            CheckResult(
                "community_export:separate_dest",
                "community-export" in body,
                "temp dest",
                "community_export_ci",
            ),
            CheckResult(
                "community_export:no_cursor_dir",
                "codestrata-cursor" in lower or "cursor" in lower,
                # job should assert absence — look for test ! -d cursor
                "test ! -d" in body and "cursor" in lower,
                "community_export_ci",
            ),
            CheckResult(
                "community_export:cursor_assert_absent",
                "codestrata-cursor" in body and "test ! -d" in body,
                "assert absent",
                "community_export_ci",
            ),
            CheckResult(
                "community_export:no_git_mutation",
                not _GIT_MUTATION.search(body),
                "no git init/push",
                "community_export_ci",
            ),
            CheckResult(
                "community_export:no_aws_configure",
                not bool(_AWS_CRED_CONFIG.search(body)),
                "no aws creds action",
                "community_export_ci",
            ),
            CheckResult(
                "community_export:invokes_12_8",
                "verification.repository_export_targets" in body,
                "authoritative verifier",
                "community_export_ci",
            ),
        ]
    )
    # Fix the broken check - remove the bad one
    checks = [c for c in checks if c.name != "community_export:no_cursor_dir"]
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "Community export CI defect",
                "community-export-verification",
                "complete",
                "incomplete",
            )
        )
    return checks, defects


def check_infrastructure_export_ci(
    inv: WorkflowInventory | None,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    body = inv.job_bodies.get("infrastructure-export-verification", "") if inv else ""
    checks.extend(
        [
            CheckResult(
                "infra_export:job_present",
                inv is not None and "infrastructure-export-verification" in inv.job_names,
                "job",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:uses_router",
                AUTHORITATIVE_EXPORT_COMMAND in body
                and "--target infrastructure" in body,
                "export_repository.py",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:dry_run",
                "--dry-run" in body,
                "dry-run",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:separate_dest",
                "infrastructure-export" in body,
                "temp dest",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:no_engine_platform_vscode",
                all(
                    tok in body
                    for tok in (
                        "test ! -d",
                        "engine",
                        "platform",
                        "vscode-plugin",
                    )
                ),
                "boundary asserts",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:pytest_cleared_pythonpath",
                (
                    'PYTHONPATH: ""' in body
                    or "PYTHONPATH=\"\"" in body
                    or "PYTHONPATH: ''" in body
                    or "PYTHONPATH=" in body  # flattened env from YAML empty string
                )
                and "PYTHONPATH=." not in body
                and "PYTHONPATH=${{" not in body,
                "empty PYTHONPATH",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:tofu_fmt",
                "tofu fmt -check -recursive" in body,
                "fmt",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:tofu_init_backend_false",
                "tofu init -backend=false" in body,
                "init",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:tofu_validate",
                "tofu validate" in body,
                "validate",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:three_roots",
                all(
                    r in body
                    for r in (
                        "modules/community-cloud-api",
                        "modules/community-data-lake",
                        "production",
                    )
                ),
                "three roots",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:no_plan_apply_destroy",
                not _PLAN_APPLY_DESTROY.search(body),
                "no plan/apply/destroy",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:no_git_mutation",
                not _GIT_MUTATION.search(body),
                "no git mutation",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:aws_scrubbed",
                "AWS_EC2_METADATA_DISABLED" in body
                and "AWS_ACCESS_KEY_ID" in body,
                "scrub",
                "infrastructure_export_ci",
            ),
            CheckResult(
                "infra_export:no_configure_aws",
                "configure-aws-credentials" not in body.lower(),
                "no oidc/creds action",
                "infrastructure_export_ci",
            ),
        ]
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "Infrastructure export CI defect",
                "infrastructure-export-verification",
                "complete",
                "incomplete",
            )
        )
    return checks, defects


def check_aws_git_permissions(
    inv: WorkflowInventory | None,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if inv is None:
        return checks, defects
    export_jobs = (
        "community-export-verification",
        "infrastructure-export-verification",
        "ci-release-boundaries",
    )
    for job in export_jobs:
        body = inv.job_bodies.get(job, "")
        # job-level permissions are in job dict — re-parse from workflow text lightly
        checks.append(
            CheckResult(
                f"perms:{job}:no_contents_write",
                "contents: write" not in body and "contents:write" not in body.replace(" ", ""),
                "read only",
                "workflow_permissions",
            )
        )
        checks.append(
            CheckResult(
                f"aws:{job}:no_configure",
                "configure-aws-credentials" not in body.lower(),
                "no aws action",
                "aws_credentials",
            )
        )
        checks.append(
            CheckResult(
                f"git:{job}:no_mutation",
                not _GIT_MUTATION.search(body),
                "no git mutation",
                "git_operations",
            )
        )
    # top-level
    checks.append(
        CheckResult(
            "perms:workflow:contents_read",
            inv.permissions.get("contents") == "read",
            str(inv.permissions),
            "workflow_permissions",
        )
    )
    checks.append(
        CheckResult(
            "perms:workflow:no_id_token_write",
            inv.permissions.get("id-token") != "write",
            str(inv.permissions),
            "workflow_permissions",
        )
    )
    # no public upload of export trees
    for job in ("community-export-verification", "infrastructure-export-verification"):
        body = inv.job_bodies.get(job, "")
        checks.append(
            CheckResult(
                f"artifacts:{job}:no_upload_export_tree",
                "upload-artifact" not in body.lower(),
                "no upload",
                "job_isolation",
            )
        )
    if not all(c.ok for c in checks if c.category == "aws_credentials"):
        defects.append(
            Defect("AWS credential boundary defect", "export jobs", "scrubbed", "configured")
        )
    if not all(c.ok for c in checks if c.category == "git_operations"):
        defects.append(
            Defect("Git permission/operation defect", "export jobs", "none", "present")
        )
    if not all(c.ok for c in checks if c.category == "workflow_permissions"):
        defects.append(
            Defect("workflow-permission defect", "ci.yml", "least privilege", "elevated")
        )
    return checks, defects


def check_job_isolation_cache_timeouts(
    inv: WorkflowInventory | None, monorepo: Path
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    if inv is None:
        return checks, defects
    text = inv.workflow_text
    # separate destinations
    community = inv.job_bodies.get("community-export-verification", "")
    infra = inv.job_bodies.get("infrastructure-export-verification", "")
    checks.append(
        CheckResult(
            "isolation:separate_destinations",
            "community-export" in community
            and "infrastructure-export" in infra
            and "community-export" not in infra
            and "infrastructure-export" not in community,
            "separate temps",
            "job_isolation",
        )
    )
    checks.append(
        CheckResult(
            "isolation:separate_jobs",
            "community-export-verification" in inv.job_names
            and "infrastructure-export-verification" in inv.job_names,
            "two jobs",
            "job_isolation",
        )
    )
    # cache: pip/npm ok; no state/plan/credentials paths as cache keys
    checks.append(
        CheckResult(
            "cache:no_state_plans",
            "tfstate" not in text.lower()
            and ".terraform/" not in text
            and "credentials.json" not in text.lower(),
            "safe caches",
            "cache",
        )
    )
    # timeouts present on jobs
    for job in REQUIRED_CI_JOBS:
        # timeout-minutes appears in workflow yaml near job
        pattern = rf"{job}:.*?timeout-minutes:\s*\d+"
        ok = bool(re.search(pattern, text, re.DOTALL))
        checks.append(
            CheckResult(f"timeout:{job}", ok, "bounded", "timeouts")
        )
    if not all(c.ok for c in checks if c.category == "job_isolation"):
        defects.append(
            Defect("job-isolation defect", "export jobs", "isolated", "shared")
        )
    if not all(c.ok for c in checks if c.category == "timeouts"):
        defects.append(
            Defect("cache/timeout defect", "jobs", "timeout-minutes", "missing")
        )
    return checks, defects


def check_release_and_versions(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # Engine / VS Code versions
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        import tomli as tomllib  # type: ignore

    engine_ver = (
        tomllib.loads((monorepo / "engine" / "pyproject.toml").read_text(encoding="utf-8"))
        .get("project", {})
        .get("version")
    )
    vscode_ver = json.loads(
        (monorepo / "vscode-plugin" / "package.json").read_text(encoding="utf-8")
    ).get("version")

    checks.append(
        CheckResult(
            "version:engine_0_2_0",
            engine_ver == INTENDED_ENGINE_VERSION,
            str(engine_ver),
            "version_boundary",
        )
    )
    checks.append(
        CheckResult(
            "version:vscode_0_2_0",
            vscode_ver == INTENDED_VSCODE_VERSION,
            str(vscode_ver),
            "version_boundary",
        )
    )
    checks.append(
        CheckResult(
            "version:assessment_schema_1_2",
            ASSESSMENT_SCHEMA_VERSION == "1.2",
            ASSESSMENT_SCHEMA_VERSION,
            "version_boundary",
        )
    )

    versions_py = (monorepo / "scripts/release/versions.py").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "version:no_cursor_in_release_versions",
            "cursor-plugin" not in versions_py and "codestrata-cursor" not in versions_py,
            "no cursor package path",
            "version_boundary",
        )
    )
    checks.append(
        CheckResult(
            "version:infra_not_tied_to_engine_tag",
            "infrastructure_version" not in versions_py
            and "codestrata-infrastructure" not in versions_py,
            "independent (not in Engine version matrix)",
            "version_boundary",
        )
    )
    inv_py = (monorepo / "scripts/release/inventory.py").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "release_inventory:vscode_present",
            "vscode-plugin/" in inv_py,
            "vscode",
            "release_inventory",
        )
    )
    checks.append(
        CheckResult(
            "release_inventory:no_cursor",
            "cursor-plugin" not in inv_py and "codestrata-cursor" not in inv_py,
            "no cursor",
            "release_inventory",
        )
    )
    checks.append(
        CheckResult(
            "release_inventory:infra_private_boundary",
            "private_infrastructure_only" in inv_py
            or "independently versioned" in inv_py.lower(),
            "infrastructure private / independent",
            "release_inventory",
        )
    )

    manifest = (monorepo / "public-export-manifest.yaml").read_text(encoding="utf-8")
    has_cursor_export_entry = bool(
        re.search(r"^\s*-\s*name:\s*codestrata-cursor\s*$", manifest, re.MULTILINE)
    )
    checks.append(
        CheckResult(
            "release_artifact:no_cursor_export",
            not has_cursor_export_entry,
            "no cursor export entry",
            "release_artifacts",
        )
    )
    checks.append(
        CheckResult(
            "release_artifact:vscode_export_present",
            "codestrata-vscode" in manifest,
            "vscode",
            "release_artifacts",
        )
    )
    checks.append(
        CheckResult(
            "release_artifact:infra_excluded_from_community",
            "- infrastructure/" in manifest or "infrastructure/" in manifest,
            "excluded from community export",
            "release_artifacts",
        )
    )
    # infrastructure remains in monorepo
    checks.append(
        CheckResult(
            "infra_source:remains_in_monorepo",
            (monorepo / "infrastructure").is_dir(),
            "infrastructure/",
            "version_boundary",
        )
    )

    if not all(c.ok for c in checks if c.category == "version_boundary"):
        defects.append(
            Defect("version-boundary defect", "versions", "0.2.0 vscode/engine", "mismatch")
        )
    if not all(c.ok for c in checks if c.category == "release_inventory"):
        defects.append(
            Defect("release-inventory defect", "inventory", "vscode only", "cursor/infra leak")
        )
    if not all(c.ok for c in checks if c.category == "release_artifacts"):
        defects.append(
            Defect("release-artifact defect", "manifest", "vscode only", "invalid")
        )
    return checks, defects


def check_publish_deploy(
    inv: WorkflowInventory | None, monorepo: Path
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Inspect executable run steps only (ignore comments forbidding plan/apply).
    run_blobs: list[str] = []
    if inv:
        for body in inv.job_bodies.values():
            run_blobs.append(body)
    joined = "\n".join(run_blobs)
    # Strip comment lines that document forbidden operations
    executable = "\n".join(
        line
        for line in joined.splitlines()
        if not line.lstrip().startswith("#")
    )
    checks.append(
        CheckResult(
            "publish:ordinary_ci_no_publish",
            not _PUBLISH.search(executable),
            "no publish cmds",
            "publish_boundary",
        )
    )
    checks.append(
        CheckResult(
            "deploy:ordinary_ci_no_plan_apply",
            not _PLAN_APPLY_DESTROY.search(executable),
            "no plan/apply/destroy",
            "deployment_boundary",
        )
    )
    checks.append(
        CheckResult(
            "deploy:no_aws_actions_in_ci",
            "configure-aws-credentials" not in executable.lower()
            or "uses: aws-actions/configure-aws-credentials" not in executable.lower(),
            "no aws actions",
            "deployment_boundary",
        )
    )
    # Stronger: uses: action must not appear
    checks[-1] = CheckResult(
        "deploy:no_aws_actions_in_ci",
        "aws-actions/configure-aws-credentials" not in executable.lower(),
        "no aws actions",
        "deployment_boundary",
    )
    slice_1210 = monorepo / "verification" / "epic12_completion"
    checks.append(
        CheckResult(
            "slice_12_10:not_started",
            not slice_1210.exists(),
            "deferred",
            "publish_boundary",
        )
    )
    if not all(c.ok for c in checks if c.category == "publish_boundary"):
        defects.append(
            Defect("publish-boundary defect", "ci.yml", "no publish", "publish present")
        )
    if not all(c.ok for c in checks if c.category == "deployment_boundary"):
        defects.append(
            Defect("deployment-boundary defect", "ci.yml", "no deploy", "deploy present")
        )
    return checks, defects


def check_determinism_surface(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    """Prefer existing authoritative verifiers rather than re-running dual export."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    # Authoritative packages exist
    for rel, name in (
        ("verification/repository_export_targets", "targets_verifier"),
        ("verification/infrastructure_repository_export", "infra_export_verifier"),
        ("verification/ci_release_boundaries", "ci_boundaries_verifier"),
    ):
        checks.append(
            CheckResult(
                f"determinism:package_{name}",
                (monorepo / rel / "__main__.py").is_file()
                or (monorepo / rel / "runner.py").is_file(),
                rel,
                "determinism",
            )
        )
    # contract says PASS_WITH_LIMITATIONS allowlist is finite
    checks.append(
        CheckResult(
            "determinism:allowlist_defined",
            len(ALLOWED_LIMITATIONS) > 0,
            "allowlist",
            "determinism",
        )
    )
    checks.append(
        CheckResult(
            "determinism:export_targets_closed",
            set(SUPPORTED_EXPORT_TARGETS) >= {"community", "infrastructure"},
            "closed set",
            "determinism",
        )
    )
    checks.append(
        CheckResult(
            "determinism:active_editors_vscode_only",
            ACTIVE_EDITOR_EXTENSIONS == ("vscode",),
            "vscode",
            "determinism",
        )
    )
    return checks, defects
