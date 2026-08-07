"""Domain completion checks for Slice 13.15 (clean_install_completion)."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_epic13_completion.checks import assemble_domain_checks
from verification.vscode_epic13_completion.models import CheckResult


def check(monorepo: Path) -> list[CheckResult]:
    """Return domain-relevant checks from the shared assembler."""
    checks, _meta = assemble_domain_checks(monorepo)
    # Filter by coarse category hints derived from module name.
    hint = "clean_install_completion".replace("_completion", "").replace("_absence", "").replace("_boundary", "")
    mapping = {
        "workflow": "workflow",
        "cli": "cli",
        "initialization": "initialization",
        "assessment": "assessment",
        "progress": "progress",
        "report": "report",
        "recovery": "recovery",
        "telemetry": "telemetry",
        "locality": "locality",
        "compatibility": "cli",
        "marketplace": "marketplace",
        "clean_install": "package_boundary",
        "cursor": "editor_inventory",
        "package": "package_boundary",
        "privacy": "privacy",
        "security": "security",
        "engine_authority": "engine_authority",
        "platform": "platform_boundary",
        "cloud": "cloud_boundary",
        "data_lake": "data_lake_boundary",
        "documentation": "documentation",
        "release_posture": "release_posture",
        "epic14": "epic14_absence",
    }
    category = mapping.get(hint, hint)
    return [c for c in checks if category in c.category]
