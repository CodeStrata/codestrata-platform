"""Athena/Glue/RDS/Redis boundary checks."""

from __future__ import annotations

import re
from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.contract import INSIGHTS_PACKAGES
from verification.community_insights_validation.inventory import package_source_blob
from verification.community_insights_validation.models import CheckResult, Defect

_ENGINE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("athena", re.compile(r"\bathena\b", re.IGNORECASE)),
    ("glue", re.compile(r"\bglue\b", re.IGNORECASE)),
    ("rds", re.compile(r"\brds\b", re.IGNORECASE)),
    ("redis", re.compile(r"\bredis\b", re.IGNORECASE)),
)


def check_athena_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for package in INSIGHTS_PACKAGES:
        blob = package_source_blob(monorepo, package)
        found = [name for name, pattern in _ENGINE_PATTERNS if pattern.search(blob)]
        add_check(
            checks,
            defects,
            f"athena:no_{Path(package).name}_engines",
            not found,
            "absent" if not found else ",".join(found),
            "athena_boundary",
        )
    return checks, defects
