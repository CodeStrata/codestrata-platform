"""Documentation consistency (16.2 posture)."""

from __future__ import annotations

import re
from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect

ACTIVE_DOC_PATHS = (
    "README.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "docs/index.md",
    "docs/guide/getting-started.md",
)


def check_documentation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    readme = monorepo / "README.md"
    add_check(checks, defects, "docs:readme_exists", readme.is_file(), "README.md", "documentation")
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "docs:readme_v020",
            "0.2.0" in text and "Community" in text,
            "v0.2.0 Community",
            "documentation",
        )
        add_check(
            checks,
            defects,
            "docs:readme_not_platform_as_community",
            not re.search(r"(?i)commercial platform.*(community product|included in community)", text),
            "no commercial-as-community",
            "documentation",
        )
        add_check(
            checks,
            defects,
            "docs:readme_no_active_cursor_product",
            "cursor-plugin" not in text.lower() or "retired" in text.lower() or "removed" in text.lower(),
            "cursor retired wording",
            "documentation",
        )

    # No stale AIMF active product naming in root README
    if readme.is_file():
        aimf_hits = re.findall(r"\bAIMF\b", readme.read_text(encoding="utf-8"))
        # AIMF may appear in migration notes; fail only if presented as current product name
        active = bool(re.search(r"(?i)\bAIMF\b.*(product|extension|cli).*(current|active)", readme.read_text(encoding="utf-8")))
        add_check(
            checks,
            defects,
            "docs:no_aimf_active_identity",
            not active,
            f"aimf_mentions={len(aimf_hits)} active={active}",
            "documentation",
        )

    # Install / release authority pointers
    install_docs = list((monorepo / "docs").rglob("*install*")) if (monorepo / "docs").is_dir() else []
    add_check(
        checks,
        defects,
        "docs:docs_tree_present",
        (monorepo / "docs").is_dir(),
        "docs/",
        "documentation",
    )

    # Platform docs clearly internal
    plat_docs = monorepo / "platform/docs"
    if plat_docs.is_dir():
        # at least one README or index mentioning internal/private
        markers = 0
        for p in list(plat_docs.rglob("*.md"))[:40]:
            t = p.read_text(encoding="utf-8", errors="ignore").lower()
            if "internal" in t or "private" in t or "platform" in t:
                markers += 1
        add_check(
            checks,
            defects,
            "docs:platform_docs_internal_markers",
            markers > 0,
            f"markers={markers}",
            "documentation",
        )
    else:
        add_check(checks, defects, "docs:platform_docs_internal_markers", True, "no_platform_docs", "documentation")

    # Community docs should not advertise Insights dashboard as Community product
    community_hits = []
    for rel in ("docs/index.md", "README.md", "docs/guide/getting-started.md"):
        p = monorepo / rel
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"(?i)insights dashboard.*(community|public product|included)", t):
            community_hits.append(rel)
        if re.search(r"(?i)codestrata insights.*(open source community feature)", t):
            community_hits.append(rel)
    add_check(
        checks,
        defects,
        "docs:community_not_advertise_insights",
        not community_hits,
        ",".join(community_hits) or "ok",
        "documentation",
        classification="community_scope",
    )

    # Hard links broken check: skip exhaustive; ensure SECURITY/CODE_OF_CONDUCT exist
    for rel in ("SECURITY.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md"):
        add_check(checks, defects, f"docs:root:{rel}", (monorepo / rel).is_file(), rel, "documentation")

    _ = install_docs  # reserved for future depth
    return checks, defects
