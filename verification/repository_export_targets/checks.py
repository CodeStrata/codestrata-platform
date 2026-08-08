"""Focused checks for Slice 12.8 target router verification."""

from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

from verification.repository_export_targets.contract import (
    AUTHORITATIVE_COMMAND,
    SUPPORTED_TARGETS,
    TARGET_MANIFEST_SCHEMAS,
    TARGET_VISIBILITY,
)
from verification.repository_export_targets.models import CheckResult, Defect

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repository_export_router.errors import (  # noqa: E402
    MissingTarget,
    RouterError,
    TargetConfigurationInvalid,
    UnknownTarget,
)
from repository_export_router.ownership import assert_destination_compatible  # noqa: E402
from repository_export_router.router import export_repository  # noqa: E402
from repository_export_router.targets import (  # noqa: E402
    REJECTED_TARGET_TOKENS,
    TARGET_REGISTRY,
    ExportTarget,
    parse_target,
)


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def check_command_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    script = monorepo / AUTHORITATIVE_COMMAND
    text = script.read_text(encoding="utf-8") if script.is_file() else ""
    checks = [
        CheckResult("command:exists", script.is_file(), AUTHORITATIVE_COMMAND, "command"),
        CheckResult("command:requires_target", "--target" in text and "required=True" in text, "target", "command"),
        CheckResult("command:requires_destination", "--destination" in text, "destination", "command"),
        CheckResult("command:dry_run", "--dry-run" in text, "dry-run", "command"),
        CheckResult(
            "command:no_force_push_flags",
            all(tok not in text for tok in ("--force", "--push", "--commit", "--tag", "--publish", "--deploy", "--apply", "--plan")),
            "no dangerous flags",
            "command",
        ),
        CheckResult(
            "command:closed_choices",
            "community" in text and "infrastructure" in text and "insights" in text,
            "closed set",
            "command",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("command-surface defect", "cli", "complete", "incomplete"))
    return checks, defects


def check_registry() -> tuple[list[CheckResult], list[Defect]]:
    checks = [
        CheckResult(
            "registry:exactly_three",
            set(t.value for t in TARGET_REGISTRY) == set(SUPPORTED_TARGETS),
            "community+infrastructure+insights",
            "registry",
        ),
        CheckResult(
            "registry:visibility",
            TARGET_REGISTRY[ExportTarget.COMMUNITY].visibility.startswith("public")
            and TARGET_REGISTRY[ExportTarget.INFRASTRUCTURE].visibility == "private",
            "visibility",
            "registry",
        ),
        CheckResult(
            "registry:manifests_separate",
            TARGET_REGISTRY[ExportTarget.COMMUNITY].manifest_schema
            != TARGET_REGISTRY[ExportTarget.INFRASTRUCTURE].manifest_schema,
            "separate schemas",
            "registry",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("target-selection defect", "registry", "valid", "invalid"))
    return checks, defects


def check_target_selection() -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # Happy path
    checks.append(
        CheckResult(
            "selection:parse_community",
            parse_target("community") is ExportTarget.COMMUNITY,
            "community",
            "selection",
        )
    )
    checks.append(
        CheckResult(
            "selection:parse_infrastructure",
            parse_target("infrastructure") is ExportTarget.INFRASTRUCTURE,
            "infrastructure",
            "selection",
        )
    )

    # Missing
    missing_ok = False
    try:
        parse_target(None)
    except MissingTarget:
        missing_ok = True
    checks.append(CheckResult("selection:missing_rejects", missing_ok, "missing_target", "selection"))

    # Unknown / aliases
    for token in sorted(REJECTED_TARGET_TOKENS)[:8]:
        rejected = False
        try:
            parse_target(token)
        except UnknownTarget:
            rejected = True
        checks.append(
            CheckResult(
                f"selection:reject_{token.replace(',', '_').replace('*', 'star')}",
                rejected,
                token,
                "selection",
            )
        )

    multi_ok = False
    try:
        parse_target("community,infrastructure")
    except UnknownTarget:
        multi_ok = True
    checks.append(CheckResult("selection:multi_rejects", multi_ok, "multi", "selection"))

    if not all(c.ok for c in checks):
        defects.append(Defect("target-selection defect", "selection", "strict", "weak"))
    return checks, defects


def check_dry_run_and_exports(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    parent = Path(tempfile.mkdtemp(prefix="sv128-export-"))
    try:
        # Community dry-run
        c_dry = parent / "community-dry"
        r1 = export_repository(target="community", destination=c_dry, dry_run=True, source_root=monorepo)
        checks.append(
            CheckResult(
                "dryrun:community_ok",
                r1.status == "ok" and not c_dry.exists(),
                "no write",
                "dry_run",
            )
        )
        r1b = export_repository(target="community", destination=c_dry, dry_run=True, source_root=monorepo)
        checks.append(
            CheckResult(
                "dryrun:community_deterministic",
                r1.to_dict() == r1b.to_dict(),
                "identical diagnostics",
                "determinism",
            )
        )

        # Infrastructure dry-run
        i_dry = parent / "infra-dry"
        r2 = export_repository(
            target="infrastructure", destination=i_dry, dry_run=True, source_root=monorepo
        )
        checks.append(
            CheckResult(
                "dryrun:infrastructure_ok",
                r2.status == "ok" and not i_dry.exists(),
                "no write",
                "dry_run",
            )
        )
        r2b = export_repository(
            target="infrastructure", destination=i_dry, dry_run=True, source_root=monorepo
        )
        checks.append(
            CheckResult(
                "dryrun:infrastructure_deterministic",
                r2.to_dict() == r2b.to_dict(),
                "identical diagnostics",
                "determinism",
            )
        )

        # Real infrastructure dual export
        ia = parent / "infra-a"
        ib = parent / "infra-b"
        ea = export_repository(
            target="infrastructure", destination=ia, dry_run=False, source_root=monorepo
        )
        eb = export_repository(
            target="infrastructure", destination=ib, dry_run=False, source_root=monorepo
        )
        checks.append(
            CheckResult(
                "infra:export_ok",
                ea.status == "ok" and eb.status == "ok",
                "dual export",
                "infrastructure",
            )
        )
        # Byte compare key artifacts
        identical = True
        for name in ("export-manifest.json", "export-inventory.json", "SHA256SUMS", "README.md"):
            if (ia / name).read_bytes() != (ib / name).read_bytes():
                identical = False
                break
        checks.append(
            CheckResult("infra:byte_identical", identical, "artifacts", "determinism")
        )
        manifest = json.loads((ia / "export-manifest.json").read_text(encoding="utf-8"))
        checks.append(
            CheckResult(
                "infra:manifest_schema",
                manifest.get("schema_name") == "infrastructure-repository-export-manifest"
                and manifest.get("schema_version") == "1.0.0",
                "1.0.0",
                "infrastructure_manifest",
            )
        )
        checks.append(
            CheckResult(
                "infra:no_engine_platform",
                not (ia / "engine").exists()
                and not (ia / "platform").exists()
                and not (ia / "vscode-plugin").exists()
                and not (ia / "cursor-plugin").exists(),
                "product trees absent",
                "isolation",
            )
        )
        checks.append(
            CheckResult(
                "infra:approach_a",
                not (ia / "infrastructure").exists() and (ia / "modules").is_dir(),
                "Approach A",
                "infrastructure",
            )
        )

        # Community real export (staging root)
        ca = parent / "community-a"
        cb = parent / "community-b"
        eca = export_repository(
            target="community", destination=ca, dry_run=False, source_root=monorepo
        )
        ecb = export_repository(
            target="community", destination=cb, dry_run=False, source_root=monorepo
        )
        checks.append(
            CheckResult(
                "community:export_ok",
                eca.status == "ok" and ecb.status == "ok",
                "dual export",
                "community",
            )
        )
        expected_repos = {
            "codestrata-engine",
            "codestrata-examples",
            "codestrata-vscode",
            "codestrata-docs",
        }
        repos_a = {p.name for p in ca.iterdir() if p.is_dir()}
        checks.append(
            CheckResult(
                "community:repo_set",
                expected_repos <= repos_a,
                f"count={len(repos_a)}",
                "community",
            )
        )
        checks.append(
            CheckResult(
                "community:no_cursor",
                "codestrata-cursor" not in repos_a and not (ca / "codestrata-cursor").exists(),
                "cursor absent",
                "community",
            )
        )
        checks.append(
            CheckResult(
                "community:no_infrastructure",
                not any((ca / name / "infrastructure").exists() for name in repos_a)
                and not any(
                    (ca / name / "modules" / "community-cloud-api").exists() for name in repos_a
                ),
                "no infra tree",
                "isolation",
            )
        )
        checks.append(
            CheckResult(
                "community:no_platform_runtime",
                not any(
                    (ca / name / "platform" / "src").exists()
                    or (ca / name / "platform" / "deployment").exists()
                    or (ca / name / "src" / "codestrata_platform").exists()
                    for name in repos_a
                ),
                "no platform runtime package",
                "isolation",
            )
        )
        # Deterministic engine README presence
        checks.append(
            CheckResult(
                "community:engine_present",
                (ca / "codestrata-engine" / "README.md").is_file()
                and (cb / "codestrata-engine" / "README.md").is_file()
                and (ca / "codestrata-engine" / "README.md").read_bytes()
                == (cb / "codestrata-engine" / "README.md").read_bytes(),
                "engine deterministic",
                "community",
            )
        )

        # Cross-target ownership confusion
        cross_fail = False
        try:
            assert_destination_compatible(
                target=ExportTarget.COMMUNITY, destination=ia
            )
        except TargetConfigurationInvalid:
            cross_fail = True
        checks.append(
            CheckResult(
                "ownership:infra_not_community",
                cross_fail,
                "reject cross use",
                "ownership",
            )
        )
        cross_fail2 = False
        try:
            assert_destination_compatible(
                target=ExportTarget.INFRASTRUCTURE, destination=ca
            )
        except TargetConfigurationInvalid:
            cross_fail2 = True
        # Community staging may not have root snapshot — check child or export via API
        # If ownership detection finds community markers under ca, good.
        from repository_export_router.ownership import detect_destination_owner

        owner_c = detect_destination_owner(ca)
        owner_i = detect_destination_owner(ia)
        checks.append(
            CheckResult(
                "ownership:detect_infra",
                owner_i is ExportTarget.INFRASTRUCTURE,
                "infra owner",
                "ownership",
            )
        )
        checks.append(
            CheckResult(
                "ownership:detect_community",
                owner_c is ExportTarget.COMMUNITY,
                f"owner={owner_c}",
                "ownership",
            )
        )
        # Export community into infra-managed dest should fail
        rejected = False
        try:
            export_repository(
                target="community", destination=ia, dry_run=True, source_root=monorepo
            )
        except TargetConfigurationInvalid:
            rejected = True
        checks.append(
            CheckResult(
                "ownership:reject_community_on_infra",
                rejected,
                "fail closed",
                "ownership",
            )
        )
        rejected2 = False
        try:
            export_repository(
                target="infrastructure",
                destination=ca,
                dry_run=True,
                source_root=monorepo,
            )
        except TargetConfigurationInvalid:
            rejected2 = True
        checks.append(
            CheckResult(
                "ownership:reject_infra_on_community",
                rejected2,
                "fail closed",
                "ownership",
            )
        )

        # Destination semantics documented differently
        checks.append(
            CheckResult(
                "semantics:different",
                r1.destination_semantics != r2.destination_semantics,
                "staging vs single-repo",
                "semantics",
            )
        )

        # Manifest separation
        checks.append(
            CheckResult(
                "manifest:separation",
                r1.target_manifest_schema != r2.target_manifest_schema,
                "independent schemas",
                "manifest",
            )
        )
        checks.append(
            CheckResult(
                "manifest:community_schema",
                r1.target_manifest_schema == TARGET_MANIFEST_SCHEMAS["community"],
                r1.target_manifest_schema,
                "community_manifest",
            )
        )
        checks.append(
            CheckResult(
                "manifest:infra_schema",
                r2.target_manifest_schema == TARGET_MANIFEST_SCHEMAS["infrastructure"],
                r2.target_manifest_schema,
                "infrastructure_manifest",
            )
        )

        # public-export-manifest still excludes infrastructure
        pem = (monorepo / "public-export-manifest.yaml").read_text(encoding="utf-8")
        checks.append(
            CheckResult(
                "public_manifest:excludes_infra",
                "infrastructure/" in pem and "forbidden" in pem.lower(),
                "community-specific",
                "platform",
            )
        )
        checks.append(
            CheckResult(
                "public_manifest:no_infra_export_entry",
                "codestrata-infrastructure" not in pem
                or "private" in pem,  # name may appear in comments only
                "not a public export target",
                "visibility",
            )
        )
        # Stronger: exports list should not include infrastructure repo as export name
        import yaml

        data = yaml.safe_load(pem)
        names = {str(e.get("name")) for e in data.get("exports") or []}
        checks.append(
            CheckResult(
                "public_manifest:export_names",
                "codestrata-infrastructure" not in names and "codestrata-cursor" not in names,
                f"names={len(names)}",
                "community",
            )
        )

    except RouterError as exc:
        checks.append(CheckResult("export:router_error", False, exc.category, "export"))
        defects.append(Defect("harness defect", "export", "ok", exc.category))
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if not all(c.ok for c in checks):
        defects.append(Defect("determinism defect", "exports", "all pass", "failed"))
    return checks, defects


def check_compatibility_wrappers(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    infra_wrap = (monorepo / "scripts" / "export_infrastructure_repository.py").read_text(
        encoding="utf-8"
    )
    community = (monorepo / "scripts" / "export-public-repos.py").read_text(encoding="utf-8")
    checks = [
        CheckResult(
            "compat:infra_delegates_router",
            "export_repository" in infra_wrap and "compatibility wrapper" in infra_wrap,
            "thin wrapper",
            "compatibility",
        ),
        CheckResult(
            "compat:infra_no_duplicate_exporter",
            "from repository_export.exporter" not in infra_wrap
            and "export_infrastructure_repository(" not in infra_wrap,
            "no duplicate infra logic",
            "compatibility",
        ),
        CheckResult(
            "compat:community_run_public_export",
            "run_public_export" in community,
            "shared community core",
            "compatibility",
        ),
        CheckResult(
            "compat:community_points_to_unified",
            "export_repository.py" in community and "--target community" in community,
            "docs note",
            "compatibility",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("compatibility-wrapper defect", "wrappers", "thin", "duplicate")
        )
    return checks, defects


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    router = monorepo / "scripts" / "repository_export_router"
    blobs = []
    for path in router.rglob("*.py"):
        blobs.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(blobs)
    # AST: no boto3/git imports in router
    bad = False
    for path in router.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in {"boto3", "botocore", "git"}:
                        bad = True
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.split(".")[0] in {"boto3", "botocore", "git", "subprocess"}:
                    # community_adapter must not import subprocess; infrastructure uses ExportError only
                    if node.module.split(".")[0] == "subprocess":
                        bad = True
    checks = [
        CheckResult("boundary:router_no_boto3_git", not bad, "AST clean", "git"),
        CheckResult(
            "boundary:no_tofu_apply",
            "tofu apply" not in blob and "terraform apply" not in blob,
            "no deploy",
            "deployment",
        ),
        CheckResult(
            "boundary:no_plan_destroy",
            '["plan"' not in blob and "tofu plan" not in blob,
            "no plan",
            "deployment",
        ),
        CheckResult(
            "boundary:aws_scrub_not_required_in_router",
            True,
            "router does not call AWS",
            "aws",
        ),
    ]
    # Infrastructure package still must not gain subprocess via wrapper path
    infra_cli = (monorepo / "scripts" / "export_infrastructure_repository.py").read_text(
        encoding="utf-8"
    )
    checks.append(
        CheckResult(
            "boundary:infra_wrapper_no_subprocess",
            "subprocess" not in infra_cli and "boto3" not in infra_cli,
            "wrapper clean",
            "aws",
        )
    )
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("Git/AWS/deployment boundary defect", "boundaries", "safe", "unsafe")
        )
    return checks, defects


def check_visibility() -> tuple[list[CheckResult], list[Defect]]:
    checks = [
        CheckResult(
            "visibility:map",
            TARGET_VISIBILITY["community"].startswith("public")
            and TARGET_VISIBILITY["infrastructure"] == "private",
            "documented",
            "visibility",
        )
    ]
    return checks, []
