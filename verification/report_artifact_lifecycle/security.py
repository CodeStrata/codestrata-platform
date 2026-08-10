"""Security checks for Slice 17.15."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import (
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
)
from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect

SECRET_PATTERNS = (
    r"ghp_[A-Za-z0-9]{20,}",
    r"github_pat_",
    r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    r"AKIA[0-9A-Z]{16}",
)

SLICE_PATHS = (
    POLICY_RELATIVE,
    REGISTER_RELATIVE,
    "platform/contracts/report_artifact_lifecycle_verification.json",
)


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"no_secrets": True}

    hits = 0
    for rel in SLICE_PATHS:
        path = monorepo / rel
        if path.is_dir():
            for file in path.rglob("*"):
                if file.is_file() and file.suffix in {".py", ".json", ".md"}:
                    text = read_text(file)
                    for pattern in SECRET_PATTERNS:
                        if re.search(pattern, text):
                            hits += 1
        elif path.is_file():
            text = read_text(path)
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, text):
                    hits += 1

    summary["no_secrets"] = hits == 0
    add_check(
        checks,
        defects,
        "security:no_secrets_in_slice",
        hits == 0,
        f"secret pattern hits={hits}",
        "security",
    )

    reg_path = monorepo / REGISTER_RELATIVE
    if reg_path.is_file():
        text = read_text(reg_path)
        add_check(
            checks,
            defects,
            "security:register_forbidden_fields",
            "forbidden_fields" in text,
            "forbidden_fields declared",
            "security",
        )

    return checks, defects, summary
