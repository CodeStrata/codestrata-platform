"""Slice 9.1–9.15 completion matrix (source/test/doc evidence)."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry_completion.models import (
    CheckResult,
    Defect,
    SliceEvidence,
)

_SLICES: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...] = (
    (
        "9.1",
        "Engine runtime foundation",
        ("engine/src/codestrata/telemetry/runtime_policy.py", "engine/src/codestrata/telemetry/events.py", "engine/src/codestrata/telemetry/projection.py"),
        ("engine/docs/telemetry-runtime.md",),
        ("engine/tests/telemetry/test_runtime_policy.py", "engine/tests/telemetry/test_runtime_events.py"),
    ),
    (
        "9.2",
        "Disabled-by-default product enforcement",
        ("engine/src/codestrata/telemetry/disabled_service.py", "engine/src/codestrata/telemetry/enforcement.py"),
        ("engine/docs/telemetry-disabled-default.md",),
        ("engine/tests/telemetry/test_disabled_default_enforcement.py",),
    ),
    (
        "9.3",
        "Process-local session consent",
        ("engine/src/codestrata/telemetry/consent.py", "engine/src/codestrata/telemetry/consent_policy.py"),
        ("engine/docs/telemetry-session-consent.md",),
        ("engine/tests/telemetry/test_session_consent_privacy.py",),
    ),
    (
        "9.4",
        "Interactive assess-only consent prompt",
        ("engine/src/codestrata/telemetry/prompt.py", "engine/src/codestrata/telemetry/prompt_policy.py"),
        ("engine/docs/telemetry-interactive-consent.md",),
        ("engine/tests/telemetry/test_interactive_consent_policy.py",),
    ),
    (
        "9.5",
        "Non-interactive suppression",
        ("engine/src/codestrata/telemetry/non_interactive.py", "engine/src/codestrata/telemetry/non_interactive_policy.py"),
        ("engine/docs/telemetry-non-interactive.md",),
        ("engine/tests/telemetry/test_non_interactive_fail_silent.py",),
    ),
    (
        "9.6",
        "Assess-only allow/deny CLI flags",
        ("engine/src/codestrata/telemetry/cli_consent.py", "engine/src/codestrata/cli/assess.py"),
        ("engine/docs/telemetry-cli-consent-flags.md",),
        ("engine/tests/telemetry/test_cli_consent_policy.py",),
    ),
    (
        "9.7",
        "Privacy-first telemetry status",
        ("engine/src/codestrata/telemetry/status_policy.py", "engine/src/codestrata/cli/telemetry_cmd.py"),
        ("engine/docs/telemetry-status.md",),
        ("engine/tests/telemetry/test_status_policy.py",),
    ),
    (
        "9.8",
        "Public event-and-field catalog",
        ("engine/src/codestrata/telemetry/catalog.py", "engine/docs/telemetry-event-catalog.json"),
        ("engine/docs/telemetry-event-catalog.md",),
        ("engine/tests/telemetry/test_catalog_artifacts.py",),
    ),
    (
        "9.9",
        "Local telemetry preview",
        ("engine/src/codestrata/telemetry/preview_builder.py", "engine/src/codestrata/telemetry/preview_policy.py"),
        ("engine/docs/telemetry-preview.md",),
        ("engine/tests/telemetry/test_preview_builder.py",),
    ),
    (
        "9.10",
        "Pre-transport privacy gate",
        ("engine/src/codestrata/telemetry/pre_transport_gate.py", "engine/src/codestrata/telemetry/pre_transport_policy.py"),
        ("engine/docs/telemetry-pre-transport-privacy.md",),
        ("engine/tests/telemetry/test_pre_transport_gate.py",),
    ),
    (
        "9.11",
        "Explicit fail-silent HTTP transport",
        ("engine/src/codestrata/telemetry/transport_factory.py", "engine/src/codestrata/telemetry/transport_policy.py"),
        ("engine/docs/telemetry-transport.md",),
        ("engine/tests/telemetry/test_transport_factory_and_boundary.py",),
    ),
    (
        "9.12",
        "Assessment lifecycle failure isolation",
        ("engine/src/codestrata/telemetry/assessment_isolation.py", "engine/src/codestrata/cli/assess.py"),
        ("engine/docs/telemetry-assessment-isolation.md",),
        ("engine/tests/telemetry/test_assessment_isolation_core.py",),
    ),
    (
        "9.13",
        "VS Code command-local telemetry runtime",
        ("vscode-plugin/src/telemetry/runtimePolicy.ts", "vscode-plugin/src/telemetry/isolation.ts"),
        ("vscode-plugin/docs/telemetry.md",),
        ("vscode-plugin/src/test/telemetryRuntime.test.ts",),
    ),
    (
        "9.14",
        "Cross-client consent and privacy verification",
        ("verification/privacy_first_telemetry/runner.py",),
        ("verification/privacy_first_telemetry/README.md",),
        ("tests/verification/privacy_first_telemetry/test_integration.py",),
    ),
    (
        "9.15",
        "Epic boundary and completion verification",
        ("verification/privacy_first_telemetry_completion/runner.py",),
        ("verification/privacy_first_telemetry_completion/README.md",),
        ("tests/verification/privacy_first_telemetry_completion/test_integration.py",),
    ),
)


def build_slice_matrix(monorepo: Path) -> tuple[list[SliceEvidence], list[CheckResult], list[Defect]]:
    matrix: list[SliceEvidence] = []
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for slice_id, purpose, impl, docs, tests in _SLICES:
        missing_impl = [p for p in impl if not (monorepo / p).exists()]
        missing_docs = [p for p in docs if not (monorepo / p).exists()]
        missing_tests = [p for p in tests if not (monorepo / p).exists()]
        ok = not missing_impl and not missing_docs and not missing_tests
        status = "complete" if ok else "incomplete"
        evidence = SliceEvidence(
            slice_id=slice_id,
            purpose=purpose,
            implementation_evidence=",".join(Path(p).name for p in impl),
            documentation_evidence=",".join(Path(p).name for p in docs),
            test_evidence=",".join(Path(p).name for p in tests),
            status=status,
        )
        matrix.append(evidence)
        check = CheckResult(
            name=f"slice_{slice_id.replace('.', '_')}_complete",
            ok=ok,
            detail=(
                "ok"
                if ok
                else f"missing_impl={missing_impl} missing_docs={missing_docs} missing_tests={missing_tests}"
            ),
            category="slices",
        )
        checks.append(check)
        if not ok:
            defects.append(
                Defect(
                    classification="missing slice evidence",
                    component=slice_id,
                    expected="complete",
                    actual="incomplete",
                    detail=check.detail,
                )
            )

    checks.append(
        CheckResult(
            name="slice_count_15",
            ok=len(matrix) == 15,
            detail=f"count={len(matrix)}",
            category="slices",
        )
    )
    return matrix, checks, defects
