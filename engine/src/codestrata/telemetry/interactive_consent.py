"""Interactive per-process telemetry consent prompt (Slice 9.4).

Asks once whether this command may attempt privacy-safe telemetry. Default is No.
Never persists, never reuses legacy consent, never creates installation identity,
and never transmits (transport remains unavailable).
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import TextIO

from codestrata.telemetry.consent import (
    TelemetrySessionConsent,
    allow_session_consent_from_interactive_prompt,
    default_session_consent,
    deny_session_consent_from_interactive_prompt,
)
from codestrata.telemetry.prompt_eligibility import (
    PromptEligibilityReason,
    evaluate_prompt_eligibility,
)
from codestrata.telemetry.prompt_policy import (
    CommunityTelemetryInteractiveConsentPolicy,
    default_interactive_consent_policy,
)
from codestrata.telemetry.prompt_result import (
    InteractiveConsentPromptResult,
    default_skipped_prompt_result,
)

PROMPT_INTRO = """\
Optional privacy-safe telemetry
-------------------------------
Telemetry is disabled by default. If you allow it, consent applies only to this
command/process and is not saved. No installation identity is created. Source
code, repository names, paths, findings, prompts, credentials, and personal
identifiers are not collected. Telemetry failures cannot block this command.
Transport is not operational in this release — allowing only prepares a
privacy-filtered session decision.
"""

PROMPT_QUESTION = "Allow privacy-safe telemetry for this command only? [y/N]: "

ALLOW_ANSWERS: frozenset[str] = frozenset({"y", "yes"})
DENY_ANSWERS: frozenset[str] = frozenset({"n", "no", ""})


class PromptAnswer(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    INVALID = "invalid"


def parse_prompt_answer(raw: str | None) -> PromptAnswer:
    """Parse a bounded answer. Only y/yes allow; empty/n/no deny; else invalid."""

    if raw is None:
        return PromptAnswer.DENY
    text = str(raw).strip().lower()
    if text in ALLOW_ANSWERS:
        return PromptAnswer.ALLOW
    if text in DENY_ANSWERS:
        return PromptAnswer.DENY
    return PromptAnswer.INVALID


def _read_line(input_func: Callable[[str], str], prompt: str) -> str:
    return input_func(prompt)


def run_interactive_consent_prompt(
    *,
    command: str,
    quiet: bool = False,
    json_output: bool = False,
    decision_already_explicit: bool = False,
    prompt_already_attempted: bool = False,
    policy: CommunityTelemetryInteractiveConsentPolicy | None = None,
    stdin_interactive: bool | None = None,
    automation_detected: bool | None = None,
    output_interactive: bool | None = None,
    input_func: Callable[[str], str] | None = None,
    echo_func: Callable[[str], None] | None = None,
    stream: TextIO | None = None,
) -> InteractiveConsentPromptResult:
    """Evaluate eligibility and optionally prompt once. Never raises to callers."""

    active = policy or default_interactive_consent_policy()
    eligibility = evaluate_prompt_eligibility(
        command=command,
        quiet=quiet,
        json_output=json_output,
        decision_already_explicit=decision_already_explicit,
        prompt_already_attempted=prompt_already_attempted,
        policy=active,
        stdin_interactive=stdin_interactive,
        automation_detected=automation_detected,
        output_interactive=output_interactive,
    )
    if not eligibility.eligible:
        ni = eligibility.non_interactive
        consent = ni.consent if ni is not None else default_session_consent()
        limitations = tuple(active.limitations)
        if ni is not None:
            limitations = tuple(sorted(set(limitations) | set(ni.limitation_codes)))
        return default_skipped_prompt_result(
            reason=eligibility.reason,
            limitations=limitations,
            consent=consent,
        )

    reader = input_func or input
    echo = echo_func
    if echo is None:

        def echo(message: str) -> None:
            target = stream
            if target is None:
                import sys

                target = sys.stderr
            try:
                target.write(message if message.endswith("\n") else message + "\n")
                target.flush()
            except Exception:
                return

    try:
        echo("")
        echo(PROMPT_INTRO.rstrip("\n"))
        echo("")
        raw = _read_line(reader, PROMPT_QUESTION)
    except EOFError:
        consent = deny_session_consent_from_interactive_prompt()
        return InteractiveConsentPromptResult(
            eligibility=True,
            eligibility_reason=PromptEligibilityReason.ELIGIBLE.value,
            prompted=True,
            attempts=1,
            decision=consent.decision.value,
            decision_source=consent.source.value,
            consent=consent,
            safe_outcome="eof_denied",
            limitation_codes=active.limitations,
        )
    except KeyboardInterrupt:
        # Telemetry is optional: treat interrupt as denial and continue product work.
        consent = deny_session_consent_from_interactive_prompt()
        return InteractiveConsentPromptResult(
            eligibility=True,
            eligibility_reason=PromptEligibilityReason.ELIGIBLE.value,
            prompted=True,
            attempts=1,
            decision=consent.decision.value,
            decision_source=consent.source.value,
            consent=consent,
            safe_outcome="interrupted_denied",
            limitation_codes=active.limitations,
        )
    except Exception:
        consent = default_session_consent()
        return InteractiveConsentPromptResult(
            eligibility=True,
            eligibility_reason=PromptEligibilityReason.ELIGIBLE.value,
            prompted=True,
            attempts=1,
            decision=consent.decision.value,
            decision_source=consent.source.value,
            consent=consent,
            safe_outcome="prompt_failed_disabled",
            limitation_codes=active.limitations,
        )

    answer = parse_prompt_answer(raw)
    # One attempt only: invalid → deny (no indefinite retry).
    if answer is PromptAnswer.ALLOW:
        consent = allow_session_consent_from_interactive_prompt()
        outcome = "allowed"
    else:
        consent = deny_session_consent_from_interactive_prompt()
        outcome = "denied" if answer is PromptAnswer.DENY else "invalid_denied"

    return InteractiveConsentPromptResult(
        eligibility=True,
        eligibility_reason=PromptEligibilityReason.ELIGIBLE.value,
        prompted=True,
        attempts=1,
        decision=consent.decision.value,
        decision_source=consent.source.value,
        consent=consent,
        safe_outcome=outcome,
        limitation_codes=active.limitations,
    )


__all__ = [
    "ALLOW_ANSWERS",
    "DENY_ANSWERS",
    "PROMPT_INTRO",
    "PROMPT_QUESTION",
    "PromptAnswer",
    "parse_prompt_answer",
    "run_interactive_consent_prompt",
]
