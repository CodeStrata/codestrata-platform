"""Report presentation: AI content labeled; no keys in html/json samples."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.helpers import (
    FORBIDDEN_REPORT_PATTERNS,
    artifact_dir,
    check,
    hard_defect,
    read_text,
)
from verification.community_ai_providers.models import CheckResult, Defect


def check_reports(
    monorepo: Path,
    *,
    repositories: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    builder = monorepo / "engine/src/codestrata/reporting/html_v2/builder.py"
    builder_text = read_text(builder) if builder.is_file() else ""
    labeled = "Modernization Advisor" in builder_text
    checks.append(
        check(
            "reports:ai_content_labeled",
            labeled,
            "Modernization Advisor label in HTML builder",
            "reports",
        )
    )
    if not labeled:
        defects.append(
            hard_defect(
                "ai_unlabeled",
                "reports:ai_content_labeled",
                "labeled",
                "missing",
            )
        )

    leak_hits: list[str] = []
    scanned = 0
    for item in repositories.get("selected") or []:
        catalog_id = str(item.get("catalog_id") or "")
        for key in (
            "github_current",
            "work_no_ai",
            "work_bedrock",
            "work_openai",
            "work_openrouter",
        ):
            base = artifact_dir(item, key, monorepo=monorepo)
            if not base:
                continue
            for name in ("assessment.html", "assessment.json", "advisor.json"):
                path = base / name
                if not path.is_file():
                    continue
                scanned += 1
                text = read_text(path)
                for pattern in FORBIDDEN_REPORT_PATTERNS:
                    if pattern.pattern.startswith("/Users/"):
                        continue
                    if pattern.search(text):
                        leak_hits.append(f"{catalog_id}:{name}")
                        break

    ok = not leak_hits
    checks.append(
        check(
            "reports:no_keys_in_samples",
            ok,
            f"scanned={scanned} leaks={len(leak_hits)}",
            "reports",
        )
    )
    if leak_hits:
        defects.append(
            hard_defect(
                "credential_in_report",
                "reports:no_keys_in_samples",
                "clean",
                ",".join(leak_hits[:5]),
            )
        )

    summary = {
        "ai_labeled": labeled,
        "sample_leaks": leak_hits[:10],
        "scanned": scanned,
    }
    return checks, defects, summary
