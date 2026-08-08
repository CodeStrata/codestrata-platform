"""Standalone repository structure validation."""

from __future__ import annotations

from pathlib import Path

from verification.repository_package_release_validation.contract import (
    RECOMMENDED_ROOT_FILES,
    REQUIRED_ROOT_FILES,
)
from verification.repository_package_release_validation.helpers import add_check
from verification.repository_package_release_validation.models import CheckResult, Defect


def check_standalone_repos(
    roots: dict[str, Path],
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {"repositories": {}}

    focus = {
        "community_engine": "codestrata-engine",
        "docs": "codestrata-docs",
        "insights": "codestrata-insights",
        "infrastructure": "codestrata-infrastructure",
        "vscode": "codestrata-vscode",
    }

    for label, key in focus.items():
        root = roots.get(key)
        entry: dict = {"key": key, "present": bool(root and root.is_dir())}
        if not root or not root.is_dir():
            add_check(checks, defects, f"standalone:present:{label}", False, key, "standalone")
            summary["repositories"][label] = entry
            continue
        add_check(checks, defects, f"standalone:present:{label}", True, key, "standalone")
        missing_required = [f for f in REQUIRED_ROOT_FILES if not (root / f).exists()]
        # Insights may generate LICENSE later — still required for releasability
        add_check(
            checks,
            defects,
            f"standalone:required_roots:{label}",
            not missing_required,
            ",".join(missing_required) or "ok",
            "standalone",
            classification="missing_release_file",
        )
        missing_rec = [f for f in RECOMMENDED_ROOT_FILES if not (root / f).exists()]
        add_check(
            checks,
            defects,
            f"standalone:recommended_roots:{label}",
            True,  # recommended — record as soft limitation via detail
            f"missing={','.join(missing_rec) or 'none'}",
            "standalone",
        )
        entry["missing_required"] = missing_required
        entry["missing_recommended"] = missing_rec

        # Community positioning / README presence already covered
        readme = (root / "README.md").read_text(encoding="utf-8", errors="ignore") if (root / "README.md").is_file() else ""
        if label in {"community_engine", "docs", "vscode"}:
            add_check(
                checks,
                defects,
                f"standalone:community_positioning:{label}",
                "codestrata" in readme.lower() or "CodeStrata" in readme,
                "README mentions CodeStrata",
                "standalone",
            )
        if label == "insights":
            add_check(
                checks,
                defects,
                f"standalone:insights_not_public_community_claim:{label}",
                "open source community edition product" not in readme.lower(),
                "insights private positioning",
                "standalone",
            )
        if label == "infrastructure":
            add_check(
                checks,
                defects,
                f"standalone:infra_private_positioning:{label}",
                "private" in readme.lower() or "infrastructure" in readme.lower(),
                "infra README",
                "standalone",
            )

        # Package manifests
        if label == "community_engine":
            add_check(
                checks,
                defects,
                f"standalone:pyproject:{label}",
                (root / "pyproject.toml").is_file(),
                "pyproject.toml",
                "standalone",
            )
        if label == "vscode":
            add_check(
                checks,
                defects,
                f"standalone:package_json:{label}",
                (root / "package.json").is_file(),
                "package.json",
                "standalone",
            )
        if label == "docs":
            add_check(
                checks,
                defects,
                f"standalone:package_json:{label}",
                (root / "package.json").is_file(),
                "package.json",
                "standalone",
            )
        if label == "insights":
            add_check(
                checks,
                defects,
                f"standalone:package_json:{label}",
                (root / "package.json").is_file(),
                "package.json",
                "standalone",
            )
        if label == "infrastructure":
            add_check(
                checks,
                defects,
                f"standalone:tofu_modules:{label}",
                (root / "modules").is_dir() or any(root.rglob("*.tf")),
                "modules/tf",
                "standalone",
            )

        summary["repositories"][label] = entry

    return checks, defects, summary
