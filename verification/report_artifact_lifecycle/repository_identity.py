"""Repository identity checks for Slice 17.15."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import ENGINE_REPOSITORY_IDENTITY
from verification.report_artifact_lifecycle.helpers import add_check, read_text, try_import_engine_module
from verification.report_artifact_lifecycle.models import CheckResult, Defect

_GITHUB_ID = re.compile(r"^github-[a-z0-9._-]+-[a-z0-9._-]+$")
_LOCAL_ID = re.compile(r"^local-[a-z0-9._-]+$")


def check_repository_identity(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"module_present": False, "api_exercised": False}

    path = monorepo / ENGINE_REPOSITORY_IDENTITY
    present = path.is_file()
    summary["module_present"] = present
    add_check(
        checks,
        defects,
        "repository_identity:module_exists",
        present,
        ENGINE_REPOSITORY_IDENTITY,
        "repository_identity",
        soft=not present,
    )

    if present:
        text = read_text(path)
        add_check(
            checks,
            defects,
            "repository_identity:github_format",
            "github-" in text or "GITHUB" in text,
            "github prefix",
            "repository_identity",
            soft=True,
        )
        add_check(
            checks,
            defects,
            "repository_identity:local_format",
            "local-" in text or "LOCAL" in text,
            "local prefix",
            "repository_identity",
            soft=True,
        )

    module, err = try_import_engine_module("codestrata.artifacts.repository_identity")
    if module is not None:
        for fn_name in ("build_repository_id", "resolve_repository_id", "sanitize_repository_id"):
            fn = getattr(module, fn_name, None)
            if callable(fn):
                try:
                    if fn_name == "build_repository_id":
                        rid = fn(owner="codestrata", repo="codestrata-platform")
                    elif fn_name == "resolve_repository_id":
                        rid = fn("github.com/codestrata/codestrata-platform")
                    else:
                        rid = fn("My Repo Name")
                    ok = bool(_GITHUB_ID.match(str(rid)) or _LOCAL_ID.match(str(rid)))
                    add_check(
                        checks,
                        defects,
                        f"repository_identity:{fn_name}",
                        ok,
                        str(rid),
                        "repository_identity",
                        soft=False if present else True,
                    )
                    summary["api_exercised"] = summary["api_exercised"] or ok
                except Exception as exc:  # noqa: BLE001
                    add_check(
                        checks,
                        defects,
                        f"repository_identity:{fn_name}",
                        False,
                        str(exc),
                        "repository_identity",
                        soft=True,
                    )
    elif present:
        add_check(
            checks,
            defects,
            "repository_identity:import",
            False,
            err or "import failed",
            "repository_identity",
            soft=True,
        )

    return checks, defects, summary
