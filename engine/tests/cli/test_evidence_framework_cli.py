from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from codestrata.cli import app


def test_evidence_plan_preview_and_run(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "app.py").write_text("print('hello')\n", encoding="utf-8")
    plan = tmp_path / "evidence-plan.yaml"
    output = tmp_path / "artifacts"
    runner = CliRunner()

    initialized = runner.invoke(
        app,
        [
            "evidence",
            "init",
            "--repo",
            str(repository),
            "--output",
            str(plan),
            "--goal",
            "Understand the evidence",
        ],
    )
    assert initialized.exit_code == 0
    assert yaml.safe_load(plan.read_text(encoding="utf-8"))["schema_version"] == "1.0"

    previewed = runner.invoke(app, ["evidence", "preview", "--plan", str(plan), "--json"])
    assert previewed.exit_code == 0
    assert json.loads(previewed.stdout)["leaves_machine"] == [
        "Nothing; every selected activity is local-only."
    ]

    executed = runner.invoke(
        app,
        [
            "evidence",
            "run",
            "--plan",
            str(plan),
            "--output",
            str(output),
            "--json",
        ],
    )
    assert executed.exit_code == 0
    payload = json.loads(executed.stdout)
    assert payload["run"]["status"] == "completed"
    assert Path(payload["report"]).is_file()


def test_evidence_help_leads_with_plan_and_studio() -> None:
    result = CliRunner().invoke(app, ["evidence", "--help"])
    assert result.exit_code == 0
    assert "Define, preview, collect, normalize, assess, and report" in result.stdout
    assert "studio" in result.stdout
