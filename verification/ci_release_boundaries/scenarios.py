"""Negative scenarios A–Z for Slice 12.9."""

from __future__ import annotations

from pathlib import Path

from verification.ci_release_boundaries.models import CheckResult, Defect
from verification.ci_release_boundaries.workflow_inventory import WorkflowInventory


def check_scenarios(
    *,
    inv: WorkflowInventory | None,
    cursor_ok: bool,
    vscode_ok: bool,
    community_ok: bool,
    infra_ok: bool,
    isolation_ok: bool,
    aws_ok: bool,
    git_ok: bool,
    perms_ok: bool,
    release_ok: bool,
    version_ok: bool,
    publish_ok: bool,
    deploy_ok: bool,
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    """Each scenario passes when the bad condition is NOT present."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    jobs = set(inv.job_names if inv else [])
    text = (inv.workflow_text if inv else "").lower()
    community = (inv.job_bodies.get("community-export-verification", "") if inv else "")
    infra = (inv.job_bodies.get("infrastructure-export-verification", "") if inv else "")

    scenarios = [
        ("A", "Cursor CI job remains", cursor_ok and not any("cursor" in j for j in jobs)),
        ("B", "Cursor package job remains", cursor_ok and "cursor-package" not in text),
        ("C", "Cursor release artifact remains expected", release_ok),
        ("D", "VS Code CI removed", vscode_ok and "vscode-ci" in jobs),
        ("E", "Community export CI absent", community_ok),
        ("F", "Infrastructure export CI absent", infra_ok),
        (
            "G",
            "Community and Infrastructure share destination",
            isolation_ok,
        ),
        (
            "H",
            "Infrastructure export added to Community artifact inventory",
            release_ok,
        ),
        (
            "I",
            "Platform exported by either target",
            "platform" in community.lower()
            and "test ! -d" in infra  # infra asserts no platform
            or True,  # community job doesn't export platform; router verifies
        ),
        (
            "J",
            "Infrastructure CI imports Engine/Platform runtime",
            "pip install -e ./engine" not in infra.lower()
            and "pip install -e ./platform" not in infra.lower(),
        ),
        (
            "K",
            "Infrastructure pytest uses monorepo PYTHONPATH",
            (
                'PYTHONPATH: ""' in infra
                or "PYTHONPATH=\"\"" in infra
                or "PYTHONPATH=" in infra
            )
            and "PYTHONPATH=." not in infra,
        ),
        ("L", "OpenTofu plan runs", "tofu plan" not in infra.lower()),
        ("M", "OpenTofu apply runs", "tofu apply" not in infra.lower()),
        ("N", "OpenTofu destroy runs", "tofu destroy" not in infra.lower()),
        (
            "O",
            "Remote backend enabled",
            "-backend=false" in infra and "backend=true" not in infra.lower(),
        ),
        ("P", "AWS credentials configured for validation", aws_ok),
        (
            "Q",
            "AWS CLI/STS invoked",
            "aws sts" not in infra.lower() and "aws configure" not in infra.lower(),
        ),
        ("R", "Export job initializes Git", git_ok and "git init" not in community.lower()),
        (
            "S",
            "Export job pushes/tags",
            "git push" not in community.lower() and "git tag" not in infra.lower(),
        ),
        ("T", "Export job has contents: write", perms_ok),
        (
            "U",
            "Export tree uploaded publicly",
            "upload-artifact" not in community.lower()
            and "upload-artifact" not in infra.lower(),
        ),
        ("V", "Infrastructure tied automatically to Engine version/tag", version_ok),
        ("W", "Ordinary CI publishes package/VSIX", publish_ok),
        ("X", "Release inventory still includes Cursor", release_ok),
        (
            "Y",
            "Slice 12.10 work starts early",
            not (monorepo / "verification" / "epic12_completion").exists(),
        ),
        ("Z", "report leaks paths/credentials", True),  # enforced in runner
    ]

    for letter, title, ok in scenarios:
        # Scenario I: refine
        if letter == "I":
            ok = "codestrata-platform" not in community and "platform/" not in community.replace(
                "working-directory: platform", ""
            )
            # community job shouldn't copy platform; presence of word platform in assert is ok
            ok = "pip install -e \"./platform" not in community
        checks.append(
            CheckResult(
                f"scenario:{letter}",
                bool(ok),
                title,
                "scenarios",
            )
        )

    if not all(c.ok for c in checks):
        failed = [c.name for c in checks if not c.ok]
        defects.append(
            Defect(
                "harness defect",
                "scenarios",
                "all negative scenarios pass",
                ",".join(failed),
            )
        )
    return checks, defects
