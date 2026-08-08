"""Community product-scope consistency for v0.2.0."""

from __future__ import annotations

import re
from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_community_scope(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    readme = (monorepo / "README.md").read_text(encoding="utf-8") if (monorepo / "README.md").is_file() else ""
    add_check(
        checks,
        defects,
        "community:mentions_engine_cli",
        bool(re.search(r"(?i)engine|cli", readme)),
        "engine/cli",
        "community_scope",
    )
    add_check(
        checks,
        defects,
        "community:mentions_vscode",
        bool(re.search(r"(?i)vs\s*code|vscode", readme)),
        "vscode",
        "community_scope",
    )
    add_check(
        checks,
        defects,
        "community:privacy_or_telemetry_documented",
        bool(re.search(r"(?i)privacy|telemetry", readme))
        or (monorepo / "SECURITY.md").is_file()
        or (monorepo / "docs").exists(),
        "privacy/telemetry",
        "community_scope",
    )

    # Must NOT expose commercial Platform / Insights as Community features in README
    bad_platform = bool(
        re.search(
            r"(?i)(commercial platform|platform portfolio|rag knowledge graph).{0,40}(community (product|edition|release))",
            readme,
        )
    )
    add_check(
        checks,
        defects,
        "community:no_commercial_platform_as_community",
        not bad_platform,
        "readme scope",
        "community_scope",
        classification="commercial_as_community",
    )

    bad_insights = bool(
        re.search(
            r"(?i)(insights dashboard|internal insights).{0,60}(community (product|feature|edition)|open.?source community)",
            readme,
        )
    )
    add_check(
        checks,
        defects,
        "community:no_insights_as_community_product",
        not bad_insights,
        "readme scope",
        "community_scope",
        classification="insights_as_community",
    )

    # Docs index similar
    idx = monorepo / "docs/index.md"
    if idx.is_file():
        t = idx.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "community:docs_index_not_platform_product",
            not re.search(r"(?i)install the commercial platform", t),
            "docs/index.md",
            "community_scope",
        )
    return checks, defects
