"""Safe cleanup of generated assessment/validation runtime artifacts (Slice 17.13).

Preserves source-controlled assets and prior-slice verification evidence under
``.codestrata-artifacts/validation/suites/sv17-12/``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from verification.community_22_repository_validation.contract import (
    ASSESSMENTS_RELATIVE,
    INTELLIGENCE_RELATIVE,
    SUITE_ID,
    VALIDATION_LOGS_RELATIVE,
    VALIDATION_REPOSITORIES_RELATIVE,
    VALIDATION_SUITES_RELATIVE,
)

PRESERVE_SUITE_IDS = frozenset({"sv17-12"})


def clean_generated_state(monorepo: Path) -> dict[str, int]:
    """Clear prior generated runtime outputs for a clean suite start.

    Returns counts of removed entries per bucket.
    """

    removed = {
        "assessments": 0,
        "intelligence": 0,
        "validation_repositories": 0,
        "validation_logs": 0,
        "other_suites": 0,
    }

    assessments = monorepo / ASSESSMENTS_RELATIVE
    if assessments.is_dir():
        for child in list(assessments.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed["assessments"] += 1

    intelligence = monorepo / INTELLIGENCE_RELATIVE
    if intelligence.is_dir():
        for child in list(intelligence.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed["intelligence"] += 1

    repos = monorepo / VALIDATION_REPOSITORIES_RELATIVE
    if repos.is_dir():
        for child in list(repos.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed["validation_repositories"] += 1

    logs = monorepo / VALIDATION_LOGS_RELATIVE
    if logs.is_dir():
        for child in list(logs.iterdir()):
            if child.name.startswith("."):
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed["validation_logs"] += 1

    suites = monorepo / VALIDATION_SUITES_RELATIVE
    if suites.is_dir():
        for child in list(suites.iterdir()):
            if child.name.startswith(".") or child.name in PRESERVE_SUITE_IDS:
                continue
            # Always recreate the active suite directory empty.
            if child.name == SUITE_ID or child.is_dir():
                if child.name == SUITE_ID:
                    shutil.rmtree(child, ignore_errors=True)
                    removed["other_suites"] += 1
                # Do not delete other historical suites unless they are the active one.
                # Only clear sv17-13; leave other suite evidence intact.
                continue

    (monorepo / ASSESSMENTS_RELATIVE).mkdir(parents=True, exist_ok=True)
    (monorepo / INTELLIGENCE_RELATIVE).mkdir(parents=True, exist_ok=True)
    (monorepo / VALIDATION_REPOSITORIES_RELATIVE).mkdir(parents=True, exist_ok=True)
    (monorepo / VALIDATION_LOGS_RELATIVE).mkdir(parents=True, exist_ok=True)
    (monorepo / VALIDATION_SUITES_RELATIVE / SUITE_ID).mkdir(parents=True, exist_ok=True)
    return removed
