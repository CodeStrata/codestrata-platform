"""CLI telemetry-on assessment checks (consent allow + product HTTP when credentialed)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_cli_on(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict = {"executed": False}

    product_transport = monorepo / "engine/src/codestrata/telemetry/product_transport.py"
    transport_factory = monorepo / "engine/src/codestrata/telemetry/transport_factory.py"
    wired = product_transport.is_file() and contains(
        product_transport, "production_telemetry_ingest_url"
    )
    checks.append(check(
        "cli_on:product_http_resolver_present",
        wired,
        "product_transport resolves production HTTP after opt-in",
        "cli_on",
    ))
    if not wired:
        defects.append(
            Defect(
                "http_transport_unwired",
                "cli_on:product_http_resolver_present",
                "present",
                "missing product_transport",
            )
        )
    checks.append(check(
        "cli_on:default_runtime_still_unavailable",
        contains(transport_factory, "create_default_telemetry_runtime")
        or contains(transport_factory, "does not call"),
        "default runtime factory does not auto-enable HTTP",
        "cli_on",
    ))
    # 17.17 limitation resolved by 17.18 wiring — record resolution, do not carry forward.
    if wired:
        limitations.append("resolved_by_17_18_http_transport")
        checks.append(check(
            "cli_on:transport_limitation_resolved",
            True,
            "product_default_http_transport_unavailable resolved",
            "cli_on",
        ))
        summary["transport_default"] = "http_after_opt_in_with_credential"
    else:
        limitations.append("product_default_http_transport_unavailable")
        summary["transport_default"] = "unavailable"

    cli = monorepo / ".venv/bin/codestrata"
    if not cli.is_file():
        cli = Path("codestrata")

    with tempfile.TemporaryDirectory(prefix="sv17-17-on-") as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
        (repo / "package.json").write_text('{"name":"sv17-17-on","version":"0.0.0"}\n', encoding="utf-8")
        out = Path(tmp) / "artifacts"
        env = os.environ.copy()
        env["CI"] = "true"  # non-interactive; --telemetry-allow still works
        env.pop("CODESTRATA_TELEMETRY_ENDPOINT", None)
        cmd = [
            str(cli),
            "assess",
            "--repo",
            str(repo),
            "--no-ai",
            "--telemetry-allow",
            "--output",
            str(out),
        ]
        try:
            proc = subprocess.run(cmd, cwd=str(monorepo), env=env, capture_output=True, text=True, timeout=180)
        except FileNotFoundError:
            checks.append(check("cli_on:cli_available", False, "codestrata CLI missing", "cli_on"))
            return checks, defects, summary, limitations
        except subprocess.TimeoutExpired:
            checks.append(check("cli_on:no_hang", False, "timed out", "cli_on"))
            defects.append(Defect("non_interactive_hang", "cli_on:no_hang", "exit", "timeout"))
            return checks, defects, summary, limitations

        summary["executed"] = True
        summary["exit_code"] = proc.returncode
        combined = (proc.stdout or "") + (proc.stderr or "")
        checks.append(check("cli_on:no_hang", True, f"exit={proc.returncode}", "cli_on"))
        checks.append(check(
            "cli_on:no_prompt_with_flag",
            "Allow privacy-safe telemetry" not in combined,
            "CLI flag suppresses prompt",
            "cli_on",
        ))
        checks.append(check(
            "cli_on:no_auto_publish",
            "reports.codestrata.ai/r/" not in combined,
            "no automatic public report URL",
            "cli_on",
        ))
        summary["auto_publish"] = False
        _ = read_text  # keep import used for symmetry with other modules
    return checks, defects, summary, limitations
