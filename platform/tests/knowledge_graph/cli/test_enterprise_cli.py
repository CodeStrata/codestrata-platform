"""CLI tests for Platform enterprise group (direct app; not Community root)."""

from __future__ import annotations

import re
from pathlib import Path

from typer.testing import CliRunner

from codestrata_platform.knowledge_graph.cli.enterprise import enterprise_app

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _visible_help(result) -> str:
    """Normalize CLI help for flag assertions (strip ANSI; collapse whitespace)."""

    raw = f"{result.stdout or ''}{result.stderr or ''}"
    return re.sub(r"\s+", " ", _ANSI_RE.sub("", raw))


def test_enterprise_help() -> None:
    result = runner.invoke(enterprise_app, ["--help"])
    assert result.exit_code == 0
    help_text = _visible_help(result)
    assert "init" in help_text
    assert "validate" in help_text
    assert "build" in help_text


def test_enterprise_init_and_validate(tmp_path: Path) -> None:
    workspace = tmp_path / "enterprise"
    config = tmp_path / "codestrata.toml"
    config.write_text(
        f"""
        [repository]
        path = "test-fixtures/sample-js-app"
        [knowledge]
        directory = "{tmp_path / "knowledge"}"
        [enterprise]
        enabled = false
        """,
        encoding="utf-8",
    )
    init = runner.invoke(
        enterprise_app,
        ["init", str(workspace)],
    )
    assert init.exit_code == 0
    validate = runner.invoke(
        enterprise_app,
        ["validate", str(workspace), "--config", str(config)],
    )
    assert validate.exit_code == 0
    build = runner.invoke(
        enterprise_app,
        ["build", str(workspace), "--config", str(config), "--json"],
    )
    assert build.exit_code == 0
    assert "graph_id" in build.stdout
