"""Negative scenarios A–Z for Slice 12.5."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_contract.contract import (
    DESTINATION_LAYOUT_DECISION,
    REPOSITORY_NAME,
    SOURCE_AUTHORITY_DECISION,
    VALIDATION_ROOTS,
)
from verification.infrastructure_repository_contract.models import CheckResult, Defect
from verification.infrastructure_repository_contract.repository_policy import (
    default_infrastructure_repository_policy,
)


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    policy = default_infrastructure_repository_policy()
    doc = (monorepo / "infrastructure" / "docs" / "repository-contract.md").read_text(
        encoding="utf-8"
    )
    never = doc.split("Never export:")[1].split("##")[0] if "Never export:" in doc else ""
    dumped = str(policy.to_stable_dict())

    cases: list[tuple[str, str, bool]] = [
        ("A", "repository purpose undefined", "Repository purpose" not in doc),
        ("B", "repository name undefined", REPOSITORY_NAME not in doc),
        ("C", "repository visibility public", policy.visibility != "private"),
        ("D", "source authority ambiguous", "pre_cutover" not in SOURCE_AUTHORITY_DECISION),
        ("E", "dual-authoring allowed", policy.dual_authoring_allowed),
        (
            "F",
            "destination layout ambiguous",
            not DESTINATION_LAYOUT_DECISION.startswith("approach_a"),
        ),
        ("G", "entire monorepo copied", "Export allowlist" not in doc or "Never export" not in doc),
        ("H", "Platform runtime included", "Platform" not in never and "platform/" not in never),
        ("I", "Engine runtime included", "Engine" not in never and "engine/" not in never),
        ("J", "VS Code included", "vscode-plugin" not in never and "VS Code" not in never),
        ("K", "Cursor included", "cursor-plugin" not in never and "Cursor" not in never),
        ("L", "Terraform state allowed", policy.state_export_allowed),
        ("M", "plan files allowed", "*.tfplan" not in doc),
        ("N", "credentials allowed", policy.credential_export_allowed),
        ("O", "local environment files allowed", ".env" not in doc),
        ("P", "generated caches allowed", "__pycache__" not in doc and "caches" not in doc.lower()),
        ("Q", "absolute paths included in manifest", "absolute paths" not in doc.lower()),
        ("R", "timestamps included in manifest", "timestamp" not in doc.lower()),
        ("S", "export script allowed to commit", policy.git_operations_allowed),
        ("T", "export script allowed to push", "push" not in doc.lower()),
        (
            "U",
            "export script allowed to tag",
            "never creates tags" not in doc and "tag" not in doc.lower(),
        ),
        (
            "V",
            "export process allowed to apply",
            policy.deployment_allowed or policy.aws_operations_allowed,
        ),
        ("W", "OpenTofu validation roots undefined", len(VALIDATION_ROOTS) < 3),
        ("X", "independent versioning undefined", "Versioning" not in doc),
        (
            "Y",
            "source deletion required before cutover",
            policy.source_deletion_before_cutover_allowed,
        ),
        (
            "Z",
            "verification report leaks paths, credentials, accounts, state, or repository URL",
            "github.com/" in dumped or "/Users/" in dumped or "AKIA" in dumped,
        ),
    ]

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
        if bad:
            defects.append(
                Defect(
                    "inventory defect",
                    f"scenario:{letter}",
                    "not present",
                    "present",
                    title,
                )
            )
    return checks, defects
