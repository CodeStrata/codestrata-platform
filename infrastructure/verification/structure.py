"""Infrastructure directory structure verification."""

from __future__ import annotations

from infrastructure.verification.contract import (
    REQUIRED_DATA_LAKE_MODULE_FILES,
    REQUIRED_MODULE_FILES,
    infra_root,
)
from infrastructure.verification.models import CheckResult


def check_structure() -> list[CheckResult]:
    root = infra_root()
    checks: list[CheckResult] = [
        CheckResult(
            name="structure:infra_root",
            ok=root.is_dir() and (root / "README.md").is_file(),
            detail="infrastructure/",
            category="structure",
        ),
        CheckResult(
            name="structure:required_dirs",
            ok=all(
                (root / rel).is_dir()
                for rel in (
                    "docs",
                    "modules/community-cloud-api",
                    "production",
                    "policies",
                    "scripts",
                    "tests",
                )
            ),
            detail="docs/modules/production/policies/scripts/tests",
            category="structure",
        ),
        CheckResult(
            name="structure:no_dev",
            ok=not (root / "dev").exists(),
            detail="no infrastructure/dev",
            category="structure",
            scenario="B",
        ),
        CheckResult(
            name="structure:no_staging",
            ok=not (root / "staging").exists(),
            detail="no infrastructure/staging",
            category="structure",
            scenario="C",
        ),
        CheckResult(
            name="structure:community_data_lake_module_present",
            ok=(root / "modules" / "community-data-lake").is_dir(),
            detail="modules/community-data-lake",
            category="structure",
            scenario="D",
        ),
        CheckResult(
            name="structure:legacy_data_lake_module_absent",
            ok=not (root / "modules" / "data-lake").exists(),
            detail="no legacy modules/data-lake",
            category="structure",
            scenario="D",
        ),
        CheckResult(
            name="structure:known_modules_only",
            ok=list((root / "modules").iterdir())
            and all(
                p.name
                in {
                    "community-cloud-api",
                    "community-data-lake",
                    "community-report-artifacts",
                    "community-insights-auth",
                }
                for p in (root / "modules").iterdir()
                if p.is_dir()
            ),
            detail="community-cloud-api, community-data-lake, community-report-artifacts, community-insights-auth",
            category="structure",
        ),
        CheckResult(
            name="structure:module_files",
            ok=all(
                (root / "modules" / "community-cloud-api" / name).is_file()
                for name in REQUIRED_MODULE_FILES
            ),
            detail=f"count={len(REQUIRED_MODULE_FILES)}",
            category="structure",
            scenario="A",
        ),
        CheckResult(
            name="structure:data_lake_module_files",
            ok=all(
                (root / "modules" / "community-data-lake" / name).is_file()
                for name in REQUIRED_DATA_LAKE_MODULE_FILES
            ),
            detail=f"count={len(REQUIRED_DATA_LAKE_MODULE_FILES)}",
            category="structure",
        ),
        CheckResult(
            name="structure:production_only_env",
            ok=(root / "production").is_dir()
            and not (root / "development").exists(),
            detail="production",
            category="structure",
        ),
        CheckResult(
            name="structure:no_engine_source_copy",
            ok=not any((root / "modules").rglob("*.py"))
            and not (root / "src").exists(),
            detail="no app python under modules",
            category="structure",
        ),
        CheckResult(
            name="structure:no_hidden_sibling_infra",
            ok=not (root.parent / "infra").exists()
            and not (root.parent / "terraform").is_dir(),
            detail="single infrastructure root",
            category="structure",
        ),
    ]
    return checks
