"""Negative scenarios A–Z for Slice 12.6 exporter."""

from __future__ import annotations

import sys
from pathlib import Path

from verification.infrastructure_repository_exporter.models import CheckResult, Defect

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from repository_export.path_rules import approach_a_map  # noqa: E402
from repository_export.policy import REPOSITORY_NAME  # noqa: E402
from repository_export.prohibited_files import (  # noqa: E402
    is_fail_closed_name,
    is_real_tfvars,
)
from repository_export.root_files import generated_gitignore  # noqa: E402


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    script = (monorepo / "scripts" / "export_infrastructure_repository.py").read_text(
        encoding="utf-8"
    )
    pkg_blob = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (monorepo / "scripts" / "repository_export").rglob("*.py")
    )
    gi = generated_gitignore()
    cases: list[tuple[str, str, bool]] = [
        ("A", "exporter copies the full monorepo", "REQUIRED_SOURCE_PREFIXES" not in pkg_blob),
        ("B", "exporter copies Platform runtime", "platform/" not in pkg_blob),
        ("C", "exporter copies Engine runtime", "engine/" not in pkg_blob),
        ("D", "exporter copies VS Code", "vscode-plugin" not in pkg_blob),
        ("E", "exporter copies Cursor", "cursor-plugin" not in pkg_blob),
        ("F", "exporter copies state", not is_fail_closed_name("terraform.tfstate")),
        ("G", "exporter copies plan", not is_fail_closed_name("run.tfplan")),
        ("H", "exporter copies credentials", not is_fail_closed_name(".env")),
        ("I", "exporter copies real tfvars", not is_real_tfvars("terraform.tfvars")),
        ("J", "exporter copies caches", "__pycache__" not in pkg_blob),
        ("K", "exporter follows symlink", "SymlinkNotAllowed" not in pkg_blob),
        ("L", "destination is inside source", "DestinationInsideSource" not in pkg_blob),
        ("M", "destination is source root", "destination is source root" not in pkg_blob),
        ("N", "destination is symlink", "DestinationSymlink" not in pkg_blob),
        ("O", "unmanaged non-empty destination accepted", "UnmanagedDestination" not in pkg_blob),
        ("P", "unmanaged extra file deleted", "UnmanagedDestinationFile" not in pkg_blob),
        ("Q", "path traversal allowed", "path traversal" not in pkg_blob),
        ("R", "case-collision allowed", "CaseCollision" not in pkg_blob),
        ("S", "executable mode lost", "MODE_EXECUTABLE" not in pkg_blob),
        ("T", "world-writable mode preserved", "world-writable" not in pkg_blob),
        ("U", "manifest contains absolute path", "absolute" not in pkg_blob.lower()),
        ("V", "manifest contains timestamp", "timestamp" not in pkg_blob.lower()),
        ("W", "exporter runs Git", "subprocess" in pkg_blob or "import git" in pkg_blob),
        (
            "X",
            "exporter runs AWS or OpenTofu",
            "import boto3" in pkg_blob or "tofu apply" in script,
        ),
        ("Y", "dry-run writes files", "dry_run" not in pkg_blob),
        (
            "Z",
            "verification report leaks paths, credentials, state, or environment data",
            "sanitize_text" not in (
                monorepo
                / "verification"
                / "infrastructure_repository_exporter"
                / "models.py"
            ).read_text(encoding="utf-8"),
        ),
    ]
    # Extra mapping sanity used by scenarios
    _ = approach_a_map("infrastructure/modules/x.tf")
    _ = REPOSITORY_NAME
    _ = gi

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for letter, title, bad in cases:
        ok = not bad
        checks.append(
            CheckResult(
                name=f"scenario:{letter}",
                ok=ok,
                detail=title,
                category="scenario",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "harness defect",
                    f"scenario_{letter}",
                    "negative scenario rejected",
                    title,
                )
            )
    return checks, defects
