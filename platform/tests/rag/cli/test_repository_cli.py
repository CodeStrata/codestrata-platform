"""CLI tests for codestrata repository grounded answering."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from codestrata.cli import app
from codestrata_platform.rag.domain.answering import AnswerConfidence, AnswerStatus

runner = CliRunner()


def test_repository_help_lists_answer() -> None:
    result = runner.invoke(app, ["repository", "--help"])
    assert result.exit_code == 0
    assert "answer" in result.stdout


def test_repository_answer_help() -> None:
    result = runner.invoke(app, ["repository", "answer", "--help"])
    assert result.exit_code == 0
    assert "--config" in result.stdout
    assert "--json" in result.stdout
    assert "Repository ID" in result.stdout


def test_repository_answer_json_with_mock(tmp_path: Path) -> None:
    config = tmp_path / "codestrata.toml"
    config.write_text(
        f"""
        [repository]
        path = "test-fixtures/sample-js-app"

        [knowledge]
        directory = "{(tmp_path / "knowledge").as_posix()}"
        enabled = true

        [knowledge.retrieval]
        enabled = true

        [knowledge.answering]
        enabled = true
        provider = "deterministic_extractive"
        """,
        encoding="utf-8",
    )

    mock_engine = MagicMock()
    mock_answer = MagicMock()
    mock_answer.summary = "Layered packages organize the codebase."
    mock_answer.confidence = AnswerConfidence.HIGH
    mock_answer.statements = ()
    mock_answer.citations = ()
    mock_result = MagicMock()
    mock_result.status = AnswerStatus.SUCCESS
    mock_result.answer = mock_answer
    mock_result.coverage = MagicMock(model_dump=lambda *, mode: {})
    mock_result.limitations = ()
    mock_result.diagnostics = ()
    mock_engine.answer.return_value = mock_result
    mock_queries = MagicMock()
    mock_queries.resolve_repository.return_value = MagicMock(
        repository_id="repo-demo",
        display_name="demo",
    )

    with (
        patch(
            "codestrata_platform.rag.cli.repository._compose_answer_engine",
            return_value=(mock_engine, mock_queries),
        ),
        patch(
            "codestrata_platform.rag.cli.repository.resolve_latest_run_id",
            return_value="scan-1",
        ),
    ):
        result = runner.invoke(
            app,
            [
                "repository",
                "answer",
                "demo",
                "How is the architecture organized?",
                "--config",
                str(config),
                "--json",
            ],
        )

    assert result.exit_code == 0
    assert '"status": "success"' in result.stdout
    assert '"repository_id": "repo-demo"' in result.stdout
    assert "Layered packages" in result.stdout
    mock_engine.answer.assert_called_once()
