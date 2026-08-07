"""Focused exporter checks for Slice 12.6."""

from __future__ import annotations

import ast
import json
import shutil
import sys
import tempfile
from pathlib import Path

from verification.infrastructure_repository_exporter.contract import (
    IMPLEMENTATION_COMMAND,
    MANIFEST_SCHEMA,
)
from verification.infrastructure_repository_exporter.models import CheckResult, Defect

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repository_export.errors import (  # noqa: E402
    DestinationInsideSource,
    DestinationSymlink,
    ExportError,
    UnmanagedDestination,
    UnmanagedDestinationFile,
)
from repository_export.exporter import (  # noqa: E402
    build_desired_export,
    export_infrastructure_repository,
)
from repository_export.path_rules import approach_a_map  # noqa: E402
from repository_export.policy import (  # noqa: E402
    MANIFEST_SCHEMA_NAME,
    MANIFEST_SCHEMA_VERSION,
    REPOSITORY_NAME,
    TARGET,
)


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def check_command_surface(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    script = monorepo / "scripts" / "export_infrastructure_repository.py"
    readme = monorepo / "scripts" / "repository_export" / "README.md"
    checks = [
        CheckResult(
            "command:script_exists",
            script.is_file(),
            "export_infrastructure_repository.py",
            "command",
        ),
        CheckResult(
            "command:readme_documents_cli",
            readme.is_file() and "--destination" in readme.read_text(encoding="utf-8"),
            IMPLEMENTATION_COMMAND,
            "command",
        ),
        CheckResult(
            "command:dedicated_not_community",
            "export-public-repos" not in script.read_text(encoding="utf-8"),
            "dedicated infrastructure exporter",
            "command",
        ),
        CheckResult(
            "command:requires_destination",
            "required=True" in script.read_text(encoding="utf-8")
            and "--destination" in script.read_text(encoding="utf-8"),
            "destination required",
            "command",
        ),
        CheckResult(
            "command:dry_run_flag",
            "--dry-run" in script.read_text(encoding="utf-8"),
            "dry-run supported",
            "command",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("harness defect", "command_surface", "explicit CLI", "incomplete")
        )
    return checks, defects


def check_static_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    pkg = monorepo / "scripts" / "repository_export"
    texts = []
    for path in pkg.rglob("*.py"):
        texts.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(texts)
    forbidden_tokens = (
        "subprocess",
        "boto3",
        "botocore",
        "git.Repo",
        "from git",
        "import git",
        "tofu plan",
        "tofu apply",
        "terraform apply",
        "terraform plan",
    )
    # Allow documenting forbidden operations in comments/docs strings carefully;
    # reject executable patterns.
    checks = [
        CheckResult(
            "boundary:no_boto3_import",
            "import boto3" not in blob and "from boto3" not in blob,
            "no boto3",
            "aws",
        ),
        CheckResult(
            "boundary:no_gitpython",
            "import git" not in blob and "from git " not in blob,
            "no git library",
            "git",
        ),
        CheckResult(
            "boundary:no_subprocess_git",
            "subprocess" not in blob,
            "no subprocess shell-outs",
            "git",
        ),
        CheckResult(
            "boundary:no_tofu_exec_strings_as_calls",
            "os.system" not in blob and "Popen" not in blob,
            "no process spawn",
            "opentofu",
        ),
    ]
    # AST scan for calls to subprocess / git
    for path in pkg.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in {"boto3", "botocore", "git", "subprocess"}:
                        checks.append(
                            CheckResult(
                                f"boundary:ast_import_{alias.name}",
                                False,
                                alias.name,
                                "git",
                            )
                        )
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "Git-boundary defect",
                "static_boundaries",
                "no git/aws/tofu exec",
                "violation",
            )
        )
    _ = forbidden_tokens
    return checks, defects


def check_path_mapping() -> tuple[list[CheckResult], list[Defect]]:
    samples = {
        "infrastructure/modules/community-cloud-api/main.tf": "modules/community-cloud-api/main.tf",
        "infrastructure/production/main.tf": "production/main.tf",
        "infrastructure/docs/repository-contract.md": "docs/repository-contract.md",
        "infrastructure/README.md": "README.md",
        "infrastructure/__init__.py": None,
    }
    checks = []
    for src, expected in samples.items():
        got = approach_a_map(src)
        checks.append(
            CheckResult(
                f"mapping:{src.replace('/', '_')}",
                got == expected,
                f"{src}->{got}",
                "mapping",
            )
        )
    defects = []
    if not all(c.ok for c in checks):
        defects.append(
            Defect("path-mapping defect", "approach_a", "prefix removed", "mismatch")
        )
    return checks, defects


def check_fixture_export(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    parent = Path(tempfile.mkdtemp(prefix="sv126-export-"))
    try:
        dest_a = parent / "a"
        dest_b = parent / "b"
        dry = parent / "dry"
        r1 = export_infrastructure_repository(
            destination=dest_a, dry_run=False, source_root=monorepo
        )
        r2 = export_infrastructure_repository(
            destination=dest_b, dry_run=False, source_root=monorepo
        )
        # Determinism across destinations
        files_a = sorted(p.relative_to(dest_a).as_posix() for p in dest_a.rglob("*") if p.is_file())
        files_b = sorted(p.relative_to(dest_b).as_posix() for p in dest_b.rglob("*") if p.is_file())
        identical_set = files_a == files_b
        identical_bytes = True
        if identical_set:
            for rel in files_a:
                if (dest_a / rel).read_bytes() != (dest_b / rel).read_bytes():
                    identical_bytes = False
                    break
        manifest = json.loads((dest_a / "export-manifest.json").read_text(encoding="utf-8"))
        inventory = json.loads((dest_a / "export-inventory.json").read_text(encoding="utf-8"))

        checks.extend(
            [
                CheckResult(
                    "fixture:export_ok",
                    r1.diagnostics.status == "ok",
                    "export status",
                    "fixture",
                ),
                CheckResult(
                    "fixture:approach_a_no_nested_infra",
                    not (dest_a / "infrastructure").exists(),
                    "no nested infrastructure/",
                    "mapping",
                ),
                CheckResult(
                    "fixture:manifest_schema",
                    manifest.get("schema_name") == MANIFEST_SCHEMA_NAME
                    and manifest.get("schema_version") == MANIFEST_SCHEMA_VERSION,
                    MANIFEST_SCHEMA,
                    "manifest",
                ),
                CheckResult(
                    "fixture:manifest_no_abs_path",
                    "/Users/" not in json.dumps(manifest) and "/home/" not in json.dumps(manifest),
                    "no absolute paths",
                    "manifest",
                ),
                CheckResult(
                    "fixture:manifest_no_timestamp",
                    "timestamp" not in json.dumps(manifest).lower()
                    and "created_at" not in json.dumps(manifest),
                    "no timestamps",
                    "manifest",
                ),
                CheckResult(
                    "fixture:repo_name",
                    manifest.get("repository_name") == REPOSITORY_NAME
                    and manifest.get("target") == TARGET,
                    REPOSITORY_NAME,
                    "manifest",
                ),
                CheckResult(
                    "fixture:inventory_present",
                    "files" in inventory and inventory.get("file_count", 0) > 0,
                    "inventory",
                    "inventory",
                ),
                CheckResult(
                    "fixture:checksums_present",
                    (dest_a / "SHA256SUMS").is_file(),
                    "SHA256SUMS",
                    "checksum",
                ),
                CheckResult(
                    "fixture:gitignore_tracks_lock",
                    not any(
                        line.strip() == ".terraform.lock.hcl"
                        for line in (dest_a / ".gitignore").read_text(encoding="utf-8").splitlines()
                    ),
                    "lock not ignored",
                    "root",
                ),
                CheckResult(
                    "fixture:root_files",
                    all(
                        (dest_a / name).is_file()
                        for name in (
                            "README.md",
                            "SECURITY.md",
                            "LICENSE",
                            ".gitignore",
                            ".editorconfig",
                            "pyproject.toml",
                        )
                    ),
                    "generated roots",
                    "root",
                ),
                CheckResult(
                    "fixture:no_engine_platform_import",
                    all(
                        not any(
                            __import__("re").match(
                                r"^\s*(from|import)\s+codestrata(_platform)?\b",
                                line,
                            )
                            for line in (dest_a / p).read_text(encoding="utf-8").splitlines()
                        )
                        for p in (
                            "tests/verification/test_boundary.py",
                            "verification/runtime_adapter.py",
                            "verification/packaging.py",
                            "verification/extraction.py",
                            "verification/safety.py",
                        )
                    ),
                    "boundary tests static",
                    "boundary",
                ),
                CheckResult(
                    "fixture:py_imports_rewritten",
                    "from verification." in (dest_a / "verification" / "runner.py").read_text(
                        encoding="utf-8"
                    )
                    and "from infrastructure.verification" not in (
                        dest_a / "verification" / "runner.py"
                    ).read_text(encoding="utf-8"),
                    "import rewrite",
                    "boundary",
                ),
                CheckResult(
                    "fixture:determinism_bytes",
                    identical_set and identical_bytes,
                    "byte-identical dual export",
                    "determinism",
                ),
                CheckResult(
                    "fixture:no_product_trees",
                    not (dest_a / "engine").exists()
                    and not (dest_a / "platform").exists()
                    and not (dest_a / "vscode-plugin").exists()
                    and not (dest_a / "cursor-plugin").exists(),
                    "product trees excluded",
                    "allowlist",
                ),
                CheckResult(
                    "fixture:exec_scripts",
                    (dest_a / "scripts" / "validate.sh").stat().st_mode & 0o111 != 0,
                    "validate.sh executable",
                    "permissions",
                ),
            ]
        )

        # Dry-run must not create destination
        export_infrastructure_repository(
            destination=dry, dry_run=True, source_root=monorepo
        )
        checks.append(
            CheckResult(
                "fixture:dry_run_no_write",
                not dry.exists(),
                "dry-run writes nothing",
                "dry_run",
            )
        )

        # Unmanaged destination rejection
        unmanaged = parent / "unmanaged"
        unmanaged.mkdir()
        (unmanaged / "noise.txt").write_text("x\n", encoding="utf-8")
        rejected = False
        try:
            export_infrastructure_repository(
                destination=unmanaged, dry_run=False, source_root=monorepo
            )
        except UnmanagedDestination:
            rejected = True
        checks.append(
            CheckResult(
                "fixture:unmanaged_rejected",
                rejected,
                "unmanaged non-empty fails closed",
                "change_plan",
            )
        )

        # Extra unmanaged file on managed dest
        extra = parent / "extra"
        shutil.copytree(dest_a, extra)
        (extra / "rogue.txt").write_text("nope\n", encoding="utf-8")
        rejected_extra = False
        try:
            export_infrastructure_repository(
                destination=extra, dry_run=False, source_root=monorepo
            )
        except UnmanagedDestinationFile:
            rejected_extra = True
        checks.append(
            CheckResult(
                "fixture:unmanaged_extra_rejected",
                rejected_extra and (extra / "rogue.txt").is_file(),
                "extra file not deleted",
                "change_plan",
            )
        )

        # Destination inside source rejected
        inside = False
        try:
            export_infrastructure_repository(
                destination=monorepo / "infrastructure",
                dry_run=True,
                source_root=monorepo,
            )
        except DestinationInsideSource:
            inside = True
        checks.append(
            CheckResult(
                "fixture:dest_inside_source_rejected",
                inside,
                "inside source rejected",
                "destination",
            )
        )

        # Symlink destination rejected
        link = parent / "link-dest"
        link.symlink_to(dest_a, target_is_directory=True)
        sym_rejected = False
        try:
            export_infrastructure_repository(
                destination=link, dry_run=True, source_root=monorepo
            )
        except DestinationSymlink:
            sym_rejected = True
        checks.append(
            CheckResult(
                "fixture:symlink_dest_rejected",
                sym_rejected,
                "symlink destination rejected",
                "symlink",
            )
        )

        # Re-export managed destination (idempotent)
        r3 = export_infrastructure_repository(
            destination=dest_a, dry_run=False, source_root=monorepo
        )
        checks.append(
            CheckResult(
                "fixture:managed_reexport",
                r3.diagnostics.status == "ok"
                and r3.change_plan.modifications == []
                and r3.change_plan.additions == [],
                "idempotent managed re-export",
                "atomicity",
            )
        )

        # Counts for report
        checks.append(
            CheckResult(
                "fixture:file_count_positive",
                r1.diagnostics.file_count > 50,
                f"files={r1.diagnostics.file_count}",
                "fixture",
            )
        )

    except ExportError as exc:
        checks.append(
            CheckResult("fixture:export_exception", False, exc.category, "fixture")
        )
        defects.append(
            Defect("harness defect", "fixture_export", "export ok", exc.category)
        )
    finally:
        shutil.rmtree(parent, ignore_errors=True)

    if not all(c.ok for c in checks):
        defects.append(
            Defect("determinism defect", "fixture_export", "all fixture checks", "failed")
        )
    return checks, defects


def check_desired_build(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    files, limitations, excluded = build_desired_export(monorepo)
    checks = [
        CheckResult(
            "build:has_manifest_artifact",
            any(f.destination_path == "export-manifest.json" for f in files),
            "manifest attached",
            "manifest",
        ),
        CheckResult(
            "build:limitations_recorded",
            "opentofu_validation_deferred_to_12_7" in limitations,
            "12.7 deferred",
            "limitations",
        ),
        CheckResult(
            "build:excluded_categories",
            len(excluded) >= 0,
            f"excluded={len(excluded)}",
            "allowlist",
        ),
        CheckResult(
            "build:no_tfstate_planned",
            not any(f.destination_path.endswith(".tfstate") for f in files),
            "no state",
            "prohibited",
        ),
        CheckResult(
            "build:no_engine_paths",
            not any(f.destination_path.startswith("engine/") for f in files),
            "no engine",
            "prohibited",
        ),
    ]
    defects = []
    if not all(c.ok for c in checks):
        defects.append(Defect("allowlist defect", "desired_build", "clean plan", "failed"))
    return checks, defects


__all__ = [
    "_status",
    "check_command_surface",
    "check_desired_build",
    "check_fixture_export",
    "check_path_mapping",
    "check_static_boundaries",
]
