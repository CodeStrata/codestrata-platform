"""CLI tests for Platform enterprise group (direct app; not Community root)."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from codestrata_platform.knowledge_graph.cli.enterprise import enterprise_app

runner = CliRunner()


def test_enterprise_help() -> None:
    result = runner.invoke(enterprise_app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "validate" in result.stdout
    assert "build" in result.stdout


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
