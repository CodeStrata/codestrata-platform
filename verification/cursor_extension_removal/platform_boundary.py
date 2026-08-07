"""Platform boundary checks after Cursor product removal."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.models import CheckResult, Defect


def check_platform_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    platform_src = monorepo / "platform" / "src"
    hits: list[str] = []
    if platform_src.is_dir():
        for path in platform_src.rglob("*.py"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            # Product import of cursor-plugin path or package is forbidden.
            if "from cursor" in text or "import cursor_plugin" in text:
                hits.append(str(path.relative_to(monorepo)))
            if "cursor-plugin/" in text and "codestrata_cursor" not in text:
                # Allow comments mentioning historical derivation.
                for line in text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    if "cursor-plugin/" in stripped and (
                        "import" in stripped or "from " in stripped
                    ):
                        hits.append(str(path.relative_to(monorepo)))
                        break
    checks.append(
        CheckResult(
            name="platform:no_cursor_product_imports",
            ok=not hits,
            detail=f"hits={hits[:5] or 'none'}",
            category="platform",
        )
    )
    if hits:
        defects.append(
            Defect(
                "Platform boundary defect",
                "platform/src",
                "no cursor product imports",
                ",".join(hits[:5]),
            )
        )

    # Infrastructure tree untouched by this slice (presence check only).
    infra = monorepo / "infrastructure"
    checks.append(
        CheckResult(
            name="platform:infrastructure_directory_present",
            ok=infra.is_dir(),
            detail=f"present={infra.is_dir()}",
            category="platform",
        )
    )
    return checks, defects
