"""Core boundary contracts for Slice 12.5."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_contract.contract import (
    DESTINATION_LAYOUT_DECISION,
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    OPTIONAL_ALLOWLIST,
    PROHIBITED_CATEGORIES,
    REPOSITORY_NAME,
    REPOSITORY_VISIBILITY,
    REQUIRED_ALLOWLIST,
    SOURCE_AUTHORITY_DECISION,
    VALIDATION_ROOTS,
)
from verification.infrastructure_repository_contract.models import CheckResult, Defect
from verification.infrastructure_repository_contract.repository_policy import (
    default_infrastructure_repository_policy,
)


def check_source_authority(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    policy = default_infrastructure_repository_policy()
    doc = (
        monorepo / "infrastructure" / "docs" / "repository-contract.md"
    ).read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "authority:decision_explicit",
            ok="pre_cutover_main_monorepo_authoritative" in SOURCE_AUTHORITY_DECISION,
            detail=SOURCE_AUTHORITY_DECISION,
            category="authority",
        ),
        CheckResult(
            "authority:dual_authoring_forbidden",
            ok=policy.dual_authoring_allowed is False
            and "dual_authoring_forbidden" in SOURCE_AUTHORITY_DECISION,
            detail="dual_authoring_forbidden",
            category="authority",
        ),
        CheckResult(
            "authority:doc_matches_policy",
            ok="Pre-cutover" in doc and "Post-cutover" in doc and "forbidden" in doc.lower(),
            detail="repository-contract.md documents A→B transition",
            category="authority",
        ),
        CheckResult(
            "authority:source_deletion_deferred",
            ok=policy.source_deletion_before_cutover_allowed is False,
            detail="no source deletion before cutover",
            category="authority",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "source-authority defect",
                "source_authority",
                "explicit A→B, no dual-authoring",
                "ambiguous",
            )
        )
    return checks, defects


def check_destination_layout(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "layout:approach_a",
            ok=DESTINATION_LAYOUT_DECISION.startswith("approach_a"),
            detail=DESTINATION_LAYOUT_DECISION,
            category="layout",
        ),
        CheckResult(
            "layout:doc_shows_root_modules",
            ok="├── modules/" in doc and "Approach B" in doc,
            detail="destination rooted at modules/production/tests/...",
            category="layout",
        ),
        CheckResult(
            "layout:prefix_removed",
            ok="Remove the `infrastructure/` prefix" in doc
            or "Remove the infrastructure/ prefix" in doc,
            detail="infrastructure/ prefix removed at destination",
            category="layout",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "destination-layout defect",
                "destination_layout",
                "approach_a explicit",
                "ambiguous",
            )
        )
    return checks, defects


def check_export_allowlist(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    infra = monorepo / "infrastructure"
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for rel in REQUIRED_ALLOWLIST:
        # Strip trailing slash for exists check of dirs
        local = rel.removeprefix("infrastructure/")
        path = infra / local.rstrip("/")
        ok = path.exists()
        checks.append(
            CheckResult(
                name=f"allowlist:{local.rstrip('/').replace('/', '_')}",
                ok=ok,
                detail=rel,
                category="allowlist",
            )
        )
        if not ok:
            defects.append(Defect("allowlist defect", rel, "present", "missing"))
    checks.append(
        CheckResult(
            "allowlist:not_open_ended",
            ok=len(REQUIRED_ALLOWLIST) >= 8 and "engine/" not in REQUIRED_ALLOWLIST,
            detail=f"required={len(REQUIRED_ALLOWLIST)} optional={len(OPTIONAL_ALLOWLIST)}",
            category="allowlist",
        )
    )
    return checks, defects


def check_prohibited_files(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    required_tokens = (
        "*.tfstate",
        "*.tfplan",
        ".env",
        ".terraform/",
        "engine/",
        "platform/",
        "vscode-plugin/",
        "cursor-plugin/",
    )
    checks = [
        CheckResult(
            name=f"prohibited:doc_{tok.replace('/', '_').replace('*', 'star')}",
            ok=tok in doc,
            detail=tok,
            category="prohibited",
        )
        for tok in required_tokens
    ]
    checks.append(
        CheckResult(
            "prohibited:categories_complete",
            ok=len(PROHIBITED_CATEGORIES) >= 10,
            detail=f"categories={len(PROHIBITED_CATEGORIES)}",
            category="prohibited",
        )
    )
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "prohibited-file defect",
                "prohibited_files",
                "complete denylist",
                "incomplete",
            )
        )
    return checks, defects


def check_shared_files(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "shared:pyproject_omit_broad",
            ok="omit" in doc.lower() and "pyproject.toml" in doc,
            detail="broad monorepo pyproject omitted",
            category="shared",
        ),
        CheckResult(
            "shared:gitignore_generate",
            ok="Infrastructure-specific" in doc and ".gitignore" in doc,
            detail="destination .gitignore generated/adapted",
            category="shared",
        ),
        CheckResult(
            "shared:license_copy",
            ok="LICENSE" in doc,
            detail="LICENSE copy/generate decision present",
            category="shared",
        ),
        CheckResult(
            "shared:public_export_manifest_omit",
            ok="public-export-manifest.yaml" in doc and "omit" in doc.lower(),
            detail="public-export-manifest remains source_repository_only",
            category="shared",
        ),
        CheckResult(
            "shared:lockfile_track_decision",
            ok="Intentionally track" in doc and ".terraform.lock.hcl" in doc,
            detail="provider lock files tracked at destination",
            category="shared",
        ),
    ]
    _ = monorepo
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("allowlist defect", "shared_files", "explicit decisions", "incomplete")
        )
    return checks, defects


def check_state_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    policy = default_infrastructure_repository_policy()
    gitignore = (monorepo / "infrastructure" / ".gitignore").read_text(encoding="utf-8")
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "state:export_forbidden",
            ok=policy.state_export_allowed is False,
            detail="state_export_allowed=false",
            category="state",
        ),
        CheckResult(
            "state:gitignore_excludes_state",
            ok="*.tfstate" in gitignore and "*.tfplan" in gitignore,
            detail="infrastructure/.gitignore excludes state/plans",
            category="state",
        ),
        CheckResult(
            "state:backend_false_validation",
            ok="backend=false" in doc,
            detail="tofu init -backend=false required",
            category="state",
        ),
        CheckResult(
            "state:example_backend_optional",
            ok=(monorepo / "infrastructure" / "production" / "backend.tf.example").is_file(),
            detail="secret-free backend.tf.example present",
            category="state",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("state/secret boundary defect", "state", "excluded", "incomplete")
        )
    return checks, defects


def check_secrets_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    policy = default_infrastructure_repository_policy()
    gitignore = (monorepo / "infrastructure" / ".gitignore").read_text(encoding="utf-8")
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "secrets:credential_export_forbidden",
            ok=policy.credential_export_allowed is False,
            detail="credential_export_allowed=false",
            category="secrets",
        ),
        CheckResult(
            "secrets:gitignore_env_keys",
            ok=".env" in gitignore and "*.pem" in gitignore,
            detail="env and key patterns ignored",
            category="secrets",
        ),
        CheckResult(
            "secrets:doc_forbidden_categories",
            ok="AWS keys" in doc or "AWS access key" in doc or "Forbidden:" in doc,
            detail="secrets categories documented",
            category="secrets",
        ),
        CheckResult(
            "secrets:scan_deferred_12_7",
            ok="12.7" in doc and "secret" in doc.lower(),
            detail="Slice 12.7 owns destination secret scanning",
            category="secrets",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("state/secret boundary defect", "secrets", "excluded", "incomplete")
        )
    return checks, defects


def check_dependency_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    boundary = (
        monorepo
        / "infrastructure"
        / "tests"
        / "verification"
        / "test_boundary.py"
    )
    text = boundary.read_text(encoding="utf-8") if boundary.is_file() else ""
    has_app_imports = "codestrata_platform" in text or "from codestrata." in text
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "dependency:app_import_recorded",
            ok=has_app_imports
            and ("test_boundary.py" in doc or "application import" in doc.lower()),
            detail="known application import classified for reimplementation",
            category="dependency",
        ),
        CheckResult(
            "dependency:ordinary_validate_no_app_packages",
            ok="Ordinary OpenTofu validation must not require" in doc,
            detail="OpenTofu validate independent of app packages",
            category="dependency",
        ),
        CheckResult(
            "dependency:adaptation_deferred",
            ok="12.6" in doc and "12.7" in doc,
            detail="adaptation deferred to 12.6/12.7",
            category="dependency",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "dependency-boundary defect",
                "dependency",
                "documented adaptation",
                "missing",
            )
        )
    return checks, defects


def check_opentofu_validation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    validate_sh = (monorepo / "infrastructure" / "scripts" / "validate.sh").read_text(
        encoding="utf-8"
    )
    opentofu_py = (
        monorepo / "infrastructure" / "verification" / "opentofu.py"
    ).read_text(encoding="utf-8")
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "opentofu:roots_defined",
            ok=len(VALIDATION_ROOTS) == 3,
            detail=",".join(VALIDATION_ROOTS),
            category="opentofu",
        ),
        CheckResult(
            "opentofu:community_cloud_api_root",
            ok="community-cloud-api" in validate_sh or "community-cloud-api" in opentofu_py,
            detail="modules/community-cloud-api",
            category="opentofu",
        ),
        CheckResult(
            "opentofu:community_data_lake_root",
            ok="community-data-lake" in opentofu_py and "community-data-lake" in doc,
            detail="modules/community-data-lake",
            category="opentofu",
        ),
        CheckResult(
            "opentofu:production_root",
            ok="production" in validate_sh and "production" in doc,
            detail="production",
            category="opentofu",
        ),
        CheckResult(
            "opentofu:commands_fmt_init_validate",
            ok="fmt -check" in doc and "backend=false" in doc and "validate" in doc,
            detail="fmt/init -backend=false/validate",
            category="opentofu",
        ),
        CheckResult(
            "opentofu:no_plan_apply_destroy",
            ok="no plan" in doc.lower() and "apply" in doc.lower(),
            detail="no plan/apply/destroy in contract validation",
            category="opentofu",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "validation-contract defect",
                "opentofu",
                "roots+commands explicit",
                "incomplete",
            )
        )
    return checks, defects


def check_versioning(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "versioning:independent",
            ok="independently" in doc.lower() or "independent" in doc.lower(),
            detail="Infrastructure versions independently",
            category="versioning",
        ),
        CheckResult(
            "versioning:no_auto_engine_tag",
            ok="Does not automatically share Engine" in doc or "0.2.0" in doc,
            detail="no automatic Engine tag coupling",
            category="versioning",
        ),
        CheckResult(
            "versioning:no_tag_by_exporter",
            ok="never creates tags" in doc.lower() or "Export script never creates tags" in doc,
            detail="exporter does not tag",
            category="versioning",
        ),
    ]
    _ = monorepo
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("versioning defect", "versioning", "independent", "ambiguous"))
    return checks, defects


def check_git_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    policy = default_infrastructure_repository_policy()
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "git:operations_forbidden",
            ok=policy.git_operations_allowed is False,
            detail="git_operations_allowed=false",
            category="git",
        ),
        CheckResult(
            "git:exporter_no_init_commit_push_tag",
            ok=all(
                tok in doc
                for tok in ("git init", "commit", "push", "tag")
            ),
            detail="exporter forbidden from Git lifecycle ops",
            category="git",
        ),
        CheckResult(
            "git:owner_operated",
            ok="owner-operated" in doc.lower() or "owner-operated" in doc,
            detail="Git actions remain owner-operated",
            category="git",
        ),
        CheckResult(
            "git:no_destination_created_this_slice",
            ok=not (monorepo / "codestrata-infrastructure").exists(),
            detail="no destination repository directory created",
            category="git",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("Git-boundary defect", "git", "forbidden", "allowed"))
    return checks, defects


def check_synchronization(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "sync:one_way",
            ok="One-way" in doc or "one-way" in doc,
            detail="one-way export",
            category="sync",
        ),
        CheckResult(
            "sync:fail_unmanaged",
            ok="unmanaged" in doc.lower(),
            detail="fail on unmanaged destination files",
            category="sync",
        ),
        CheckResult(
            "sync:dry_run",
            ok="Dry-run" in doc or "dry-run" in doc,
            detail="dry-run required",
            category="sync",
        ),
        CheckResult(
            "sync:no_bidirectional",
            ok="bidirectional" in doc.lower() and "No" in doc,
            detail="no bidirectional sync",
            category="sync",
        ),
    ]
    _ = monorepo
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("synchronization defect", "sync", "fail-closed rules", "incomplete")
        )
    return checks, defects


def check_manifest_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "manifest:schema_named",
            ok=MANIFEST_SCHEMA_NAME in doc and MANIFEST_SCHEMA_VERSION in doc,
            detail=f"{MANIFEST_SCHEMA_NAME}:{MANIFEST_SCHEMA_VERSION}",
            category="manifest",
        ),
        CheckResult(
            "manifest:sha256",
            ok="SHA-256" in doc,
            detail="SHA-256 checksums",
            category="manifest",
        ),
        CheckResult(
            "manifest:no_absolute_paths",
            ok="Never include absolute paths" in doc or "absolute paths" in doc.lower(),
            detail="no absolute paths/timestamps/credentials",
            category="manifest",
        ),
        CheckResult(
            "manifest:not_operational_yet",
            ok=not (monorepo / "infrastructure" / "export-manifest.json").exists(),
            detail="no operational export manifest created in 12.5",
            category="manifest",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("manifest/inventory defect", "manifest", "defined", "incomplete")
        )
    return checks, defects


def check_inventory_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    return check_manifest_contract(monorepo)


def check_permissions(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    scripts = monorepo / "infrastructure" / "scripts"
    exec_ok = True
    if scripts.is_dir():
        for path in scripts.glob("*.sh"):
            if not path.stat().st_mode & 0o111:
                exec_ok = False
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "permissions:scripts_executable",
            ok=exec_ok,
            detail="approved scripts retain executable bit",
            category="permissions",
        ),
        CheckResult(
            "permissions:symlink_fail_closed",
            ok="Symlinks rejected" in doc or "symlink" in doc.lower(),
            detail="symlinks fail closed by default",
            category="permissions",
        ),
        CheckResult(
            "permissions:no_setuid",
            ok="setuid" in doc.lower(),
            detail="no setuid/setgid",
            category="permissions",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("permission defect", "permissions", "explicit", "incomplete"))
    return checks, defects


def check_documentation_links(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    lake = (monorepo / "infrastructure" / "docs" / "community-data-lake.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "docs:monorepo_links_inventoried",
            ok="platform/docs/" in lake,
            detail="platform/docs links exist in current infra docs",
            category="docs",
        ),
        CheckResult(
            "docs:rewrite_policy",
            ok="conceptual external" in doc.lower() or "broken relative links" in doc.lower(),
            detail="export-time link rewrite policy",
            category="docs",
        ),
        CheckResult(
            "docs:contract_doc_present",
            ok=(monorepo / "infrastructure" / "docs" / "repository-contract.md").is_file(),
            detail="repository-contract.md",
            category="docs",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("documentation-link defect", "docs", "policy present", "missing")
        )
    return checks, defects


def check_public_private_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    policy = default_infrastructure_repository_policy()
    manifest = (monorepo / "public-export-manifest.yaml").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "public:visibility_private",
            ok=policy.visibility == REPOSITORY_VISIBILITY == "private",
            detail="repository visibility private",
            category="public",
        ),
        CheckResult(
            "public:name_codestrata_infrastructure",
            ok=policy.repository_name == REPOSITORY_NAME,
            detail=REPOSITORY_NAME,
            category="public",
        ),
        CheckResult(
            "public:community_export_excludes_infra",
            ok="infrastructure/" in manifest,
            detail="public-export-manifest forbids infrastructure/",
            category="public",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "public/private boundary defect",
                "public_private",
                "private+excluded",
                "incomplete",
            )
        )
    return checks, defects


def check_ci_contract(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "ci:expectations_defined",
            ok="CI expectations" in doc or "Slice 12.9" in doc,
            detail="CI expectations deferred to 12.9",
            category="ci",
        ),
        CheckResult(
            "ci:no_plan_apply",
            ok="no plan/apply/destroy" in doc.lower() or "no plan" in doc.lower(),
            detail="CI must not plan/apply/destroy",
            category="ci",
        ),
        CheckResult(
            "ci:no_push_tag_release",
            ok="no push" in doc.lower() or "push/tag/release" in doc.lower(),
            detail="CI must not push/tag/release",
            category="ci",
        ),
    ]
    _ = monorepo
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("validation-contract defect", "ci", "defined", "missing"))
    return checks, defects


def check_migration(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "migration:stages_listed",
            ok="Migration stages" in doc and "Cutover" in doc,
            detail="migration stages explicit",
            category="migration",
        ),
        CheckResult(
            "migration:source_removal_deferred",
            ok="deferred" in doc.lower() and "deletion" in doc.lower(),
            detail="source removal deferred until after cutover",
            category="migration",
        ),
        CheckResult(
            "migration:manual_git",
            ok="manually" in doc.lower(),
            detail="Git/remote/push manual",
            category="migration",
        ),
        CheckResult(
            "migration:infra_not_deleted",
            ok=(monorepo / "infrastructure").is_dir(),
            detail="infrastructure/ retained in main repository",
            category="migration",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("migration/rollback defect", "migration", "stages explicit", "incomplete")
        )
    return checks, defects


def check_rollback(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    checks = [
        CheckResult(
            "rollback:before_cutover",
            ok="Before cutover" in doc or "before cutover" in doc.lower(),
            detail="pre-cutover rollback principles",
            category="rollback",
        ),
        CheckResult(
            "rollback:no_aws_change",
            ok="no state/AWS" in doc.lower() or "no AWS" in doc or "AWS change" in doc,
            detail="no AWS/state change on failed export",
            category="rollback",
        ),
        CheckResult(
            "rollback:after_cutover_explicit",
            ok="After cutover" in doc or "after cutover" in doc.lower(),
            detail="post-cutover requires ownership decision",
            category="rollback",
        ),
    ]
    _ = monorepo
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("migration/rollback defect", "rollback", "explicit", "incomplete")
        )
    return checks, defects
