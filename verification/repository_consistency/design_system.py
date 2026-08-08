"""Design System authority consistency."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_design_system(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    ds = monorepo / "design-system"
    add_check(checks, defects, "design:root_exists", ds.is_dir(), "design-system/", "design_system")
    tokens = ds / "tokens/tokens.css"
    add_check(checks, defects, "design:tokens_master", tokens.is_file(), "tokens.css", "design_system")

    # No second design-system root
    rivals = [
        p
        for p in monorepo.iterdir()
        if p.is_dir() and p.name.lower() in {"design_system", "designsystem", "ui-kit", "styleguide"}
    ]
    add_check(
        checks,
        defects,
        "design:no_second_system",
        not rivals,
        ",".join(p.name for p in rivals) or "none",
        "design_system",
    )

    # No Georgia as active authority in live tokens
    if tokens.is_file():
        t = tokens.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "design:no_georgia_authority",
            "Georgia" not in t,
            "tokens.css",
            "design_system",
        )
        add_check(
            checks,
            defects,
            "design:no_amber_primary_authority",
            "#d98a3d" not in t.lower() and "--amber:" not in t.lower(),
            "tokens.css",
            "design_system",
        )

    # Docs bridge must not import sibling design-system path
    bridge = monorepo / "docs/.vitepress/theme/tokens.css"
    if bridge.is_file():
        bt = bridge.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "design:docs_no_sibling_import",
            "../design-system/" not in bt and "../../design-system/" not in bt and "../../../design-system/" not in bt,
            "docs theme tokens",
            "design_system",
            classification="design_consumer_as_master",
        )
        add_check(
            checks,
            defects,
            "design:docs_uses_packaged_tokens",
            "design-tokens" in bt or "public/design-tokens" in bt,
            "packaged tokens",
            "design_system",
        )
    return checks, defects
