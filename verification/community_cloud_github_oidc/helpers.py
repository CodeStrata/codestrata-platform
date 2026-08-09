"""Helpers for Slice 17.3."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from verification.community_cloud_github_oidc.models import CheckResult, Defect


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def add_check(
    checks: list[CheckResult],
    defects: list[Defect],
    check_id: str,
    ok: bool,
    detail: str,
    category: str,
    *,
    classification: str | None = None,
) -> None:
    checks.append(CheckResult(check_id, bool(ok), detail, category))
    if not ok:
        defects.append(Defect(classification or category, check_id, "pass", detail))


def run_aws(args: list[str], *, timeout: int = 60) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["AWS_PROFILE"] = env.get("AWS_PROFILE") or "codestrata_infra"
    env["AWS_REGION"] = env.get("AWS_REGION") or "us-west-2"
    env["AWS_DEFAULT_REGION"] = env.get("AWS_DEFAULT_REGION") or env["AWS_REGION"]
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
        env.pop(k, None)
    try:
        proc = subprocess.run(
            ["aws", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            check=False,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:  # noqa: BLE001
        return 99, "", type(exc).__name__


def sanitize_text(text: str) -> str:
    text = re.sub(r"\barn:aws:[^\s\"']+", "[arn-redacted]", text)
    text = re.sub(r"\b\d{12}\b", "[account-redacted]", text)
    text = re.sub(r"/Users/[^\s\"']+", "[path-redacted]", text)
    text = re.sub(r"/home/[^\s\"']+", "[path-redacted]", text)
    return text
