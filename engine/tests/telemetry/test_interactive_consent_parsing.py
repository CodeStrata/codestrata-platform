"""Answer parsing and consent mapping (Slice 9.4)."""

from __future__ import annotations

from codestrata.telemetry.decisions import TelemetryDecision, TelemetryDecisionSource
from codestrata.telemetry.interactive_consent import (
    PromptAnswer,
    parse_prompt_answer,
    run_interactive_consent_prompt,
)


def test_parse_allow_deny_invalid() -> None:
    assert parse_prompt_answer("y") is PromptAnswer.ALLOW
    assert parse_prompt_answer(" YES ") is PromptAnswer.ALLOW
    assert parse_prompt_answer("n") is PromptAnswer.DENY
    assert parse_prompt_answer("") is PromptAnswer.DENY
    assert parse_prompt_answer(None) is PromptAnswer.DENY
    assert parse_prompt_answer("true") is PromptAnswer.INVALID
    assert parse_prompt_answer("1") is PromptAnswer.INVALID
    assert parse_prompt_answer("enable") is PromptAnswer.INVALID


def test_B_C_empty_and_invalid_never_allow() -> None:
    empty = run_interactive_consent_prompt(
        command="assess",
        stdin_interactive=True,
        automation_detected=False,
        input_func=lambda _p: "",
        echo_func=lambda _m: None,
    )
    assert empty.decision == TelemetryDecision.DENIED_FOR_SESSION.value
    assert empty.decision_source == TelemetryDecisionSource.INTERACTIVE_PROMPT.value
    assert empty.consent.transmission_authorized is False

    invalid = run_interactive_consent_prompt(
        command="assess",
        stdin_interactive=True,
        automation_detected=False,
        input_func=lambda _p: "true",
        echo_func=lambda _m: None,
    )
    assert invalid.decision == TelemetryDecision.DENIED_FOR_SESSION.value
    assert invalid.safe_outcome == "invalid_denied"


def test_yes_maps_to_allowed_interactive() -> None:
    result = run_interactive_consent_prompt(
        command="assess",
        stdin_interactive=True,
        automation_detected=False,
        input_func=lambda _p: "y",
        echo_func=lambda _m: None,
    )
    assert result.prompted is True
    assert result.decision == TelemetryDecision.ALLOWED_FOR_SESSION.value
    assert result.decision_source == TelemetryDecisionSource.INTERACTIVE_PROMPT.value
    assert result.consent.persisted is False
    payload = result.to_stable_dict()
    assert "raw_answer" not in payload
    assert "answer" not in payload
    assert "response" not in payload
    assert "yes" not in payload.get("safe_outcome", "")
