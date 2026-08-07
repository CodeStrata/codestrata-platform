"""Engine telemetry / analytics boundary checks (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def check_engine_telemetry(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    telemetry_root = monorepo / "engine" / "src" / "codestrata" / "telemetry"
    blob = ""
    if telemetry_root.is_dir():
        for path in sorted(telemetry_root.rglob("*.py")):
            blob += path.read_text(encoding="utf-8", errors="ignore")
    # Engine must not construct cursor_extension telemetry.
    constructs_cursor = 'client_name = "cursor_extension"' in blob or 'client_name="cursor_extension"' in blob
    emits_cli = "codestrata_cli" in blob
    checks.append(
        CheckResult(
            "engine_telemetry:no_cursor_construction",
            ok=not constructs_cursor,
            detail="no cursor_extension client construction",
            category="engine_telemetry",
        )
    )
    checks.append(
        CheckResult(
            "engine_telemetry:cli_present",
            ok=emits_cli or not telemetry_root.is_dir(),
            detail="codestrata_cli remains in telemetry vocabulary",
            category="engine_telemetry",
        )
    )
    if constructs_cursor:
        defects.append(
            Defect(
                "Engine telemetry/analytics regression",
                "engine/telemetry",
                "no cursor construction",
                "cursor construction present",
            )
        )
    return checks, defects


def check_engine_analytics(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    analytics = (
        monorepo
        / "engine"
        / "src"
        / "codestrata"
        / "telemetry"
        / "analytics"
        / "events.py"
    )
    text = analytics.read_text(encoding="utf-8") if analytics.is_file() else ""
    approved = '_APPROVED_CLIENTS: frozenset[str] = frozenset({"codestrata_cli", "vscode_extension"})'
    ok = approved in text or (
        "codestrata_cli" in text and "vscode_extension" in text and "cursor_extension" not in text
    )
    # cursor may appear only in comments; reject active frozenset membership.
    active_has_cursor = '"cursor_extension"' in text and "_APPROVED_CLIENTS" in text
    if active_has_cursor:
        # Verify cursor is not inside the approved frozenset literal.
        start = text.find("_APPROVED_CLIENTS")
        snippet = text[start : start + 200] if start >= 0 else ""
        ok = "cursor_extension" not in snippet
    checks.append(
        CheckResult(
            "engine_analytics:approved_clients_exclude_cursor",
            ok=ok,
            detail="Anonymous Analytics approved clients exclude cursor",
            category="engine_analytics",
        )
    )
    if not ok:
        defects.append(
            Defect(
                "Engine telemetry/analytics regression",
                "analytics/events.py",
                "cursor absent from approved clients",
                "cursor present",
            )
        )
    return checks, defects
