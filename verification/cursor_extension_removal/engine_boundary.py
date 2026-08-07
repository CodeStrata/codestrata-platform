"""Engine boundary checks after Cursor product removal."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.models import CheckResult, Defect

_FORBIDDEN_IMPORT_TOKENS = (
    "cursor-plugin",
    "codestrata-cursor",
    "codestrata.cursor",
)


def check_engine_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    engine_src = monorepo / "engine" / "src"
    hits: list[str] = []
    if engine_src.is_dir():
        for path in engine_src.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for token in _FORBIDDEN_IMPORT_TOKENS:
                if token in text:
                    hits.append(f"{path.relative_to(monorepo)}:{token}")
                    break
    checks.append(
        CheckResult(
            name="engine:no_cursor_product_imports",
            ok=not hits,
            detail=f"hits={hits[:5] or 'none'}",
            category="engine",
        )
    )
    if hits:
        defects.append(
            Defect("Engine boundary defect", "engine/src", "no cursor imports", ",".join(hits[:5]))
        )

    # Assessment schema pin
    assessment_hits = []
    for rel in (
        "engine/src/codestrata/reporting/contract/constants.py",
        "engine/src/codestrata/reporting/contract/identifiers.py",
    ):
        path = monorepo / rel
        if path.is_file() and "1.2" in path.read_text(encoding="utf-8", errors="ignore"):
            assessment_hits.append(rel)
    checks.append(
        CheckResult(
            name="engine:assessment_schema_1_2_present",
            ok=bool(assessment_hits),
            detail=f"files={assessment_hits}",
            category="engine",
        )
    )
    return checks, defects
