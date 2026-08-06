"""Legacy state isolation for interactive consent (Slice 9.4)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from codestrata.telemetry.decisions import TelemetryDecision
from codestrata.telemetry.service import (
    ensure_interactive_product_telemetry,
    get_legacy_telemetry_service,
    reset_telemetry_singletons,
)


def test_E_F_legacy_prefs_do_not_control_prompt(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    (home / "telemetry.json").write_text(
        json.dumps({"enabled": True, "decision_made": True, "schema_version": "1.0.0"}),
        encoding="utf-8",
    )
    (home / "installation_id").write_text(
        "55555555-5555-4555-8555-555555555555\n", encoding="utf-8"
    )
    before = {p.name: p.read_bytes() for p in home.iterdir()}
    monkeypatch.setenv("CODESTRATA_HOME", str(home))
    reset_telemetry_singletons()

    with patch("codestrata.telemetry.preferences.load_preferences") as load:
        telemetry = ensure_interactive_product_telemetry(
            command="assess",
            stdin_interactive=True,
            automation_detected=False,
            input_func=lambda _p: "n",
            echo_func=lambda _m: None,
        )
        load.assert_not_called()

    assert telemetry.runtime.session.decision is TelemetryDecision.DENIED_FOR_SESSION
    assert {p.name: p.read_bytes() for p in home.iterdir()} == before


def test_legacy_enable_does_not_skip_current_prompt_decision(
    tmp_path: Path, monkeypatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("CODESTRATA_HOME", str(home))
    reset_telemetry_singletons()
    get_legacy_telemetry_service(home=home).enable(emit_events=False)
    reset_telemetry_singletons()
    telemetry = ensure_interactive_product_telemetry(
        command="assess",
        stdin_interactive=True,
        automation_detected=False,
        input_func=lambda _p: "y",
        echo_func=lambda _m: None,
    )
    assert telemetry.runtime.session.decision is TelemetryDecision.ALLOWED_FOR_SESSION
    assert (
        telemetry.runtime.session.decision_source.value == "interactive_prompt"
    )
