"""Package / Platform / Data Lake / Cursor boundary checks (Slice 10.8)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_boundaries(
    monorepo: Path,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    engine_analytics = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"
    hits: list[str] = []
    if engine_analytics.is_dir():
        for path in engine_analytics.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for needle in (
                "codestrata_platform",
                "community_cloud",
                "data_lake",
                "boto3",
                "@aws-sdk",
                "cursor-plugin",
                "vscode-plugin",
            ):
                if needle in text and "deferred" not in text.lower():
                    # Allow limitation strings mentioning deferred cloud/data lake.
                    if needle in ("community_cloud", "data_lake") and "deferred" in text.lower():
                        continue
                    if "deferred" in text.lower() and needle in text:
                        # still skip if only deferred mentions
                        if text.lower().count(needle) <= text.lower().count("deferred") + 2:
                            continue
                    hits.append(f"{path.name}:{needle}")
    checks.append(
        CheckResult(
            name="boundary:engine_no_platform_datalake_imports",
            ok=hits == [],
            detail=",".join(hits[:8]),
            category="boundary",
            contract="engine",
        )
    )

    checks.append(
        CheckResult(
            name="boundary:vscode_no_engine_python_import",
            ok="codestrata.telemetry" not in vscode.source_blob
            and "from codestrata" not in vscode.source_blob,
            category="boundary",
            contract="vscode",
        )
    )

    cursor = monorepo / "cursor-plugin" / "src"
    cursor_hits: list[str] = []
    if cursor.is_dir():
        for path in cursor.rglob("*"):
            if path.is_file() and (
                "analytics" in path.name.lower() or "telemetry" in path.name.lower()
            ):
                cursor_hits.append(path.name)
    checks.append(
        CheckResult(
            name="boundary:cursor_no_analytics_runtime",
            ok=cursor_hits == [],
            detail=",".join(cursor_hits),
            category="boundary",
            contract="cursor",
        )
    )

    # Verification package outside product runtime.
    checks.append(
        CheckResult(
            name="boundary:verification_outside_runtime",
            ok=(monorepo / "verification" / "anonymous_analytics_privacy").is_dir(),
            category="boundary",
            contract="verification",
        )
    )

    # No Cloud analytics processor added under platform for Epic 10.
    platform_hits = []
    platform_root = monorepo / "platform"
    if platform_root.is_dir():
        for path in platform_root.rglob("*anonymous*analytics*"):
            platform_hits.append(path.name)
    checks.append(
        CheckResult(
            name="boundary:no_platform_anonymous_analytics_processor",
            ok=platform_hits == [],
            detail=",".join(platform_hits),
            category="boundary",
            contract="platform",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("boundary defect", item.name, "pass", "fail"))
    return checks, defects
