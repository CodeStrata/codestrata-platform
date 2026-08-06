"""Slice 10.1–10.9 completion matrix (source/test/doc/verification evidence)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.models import (
    CheckResult,
    Defect,
    SliceEvidence,
)

# (slice_id, purpose, impl_paths, doc_paths, test_paths, verification_paths)
_SLICES: tuple[
    tuple[str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]],
    ...,
] = (
    (
        "10.1",
        "Anonymous analytics contract",
        (
            "engine/src/codestrata/telemetry/analytics/policy.py",
            "engine/src/codestrata/telemetry/analytics/events.py",
            "engine/src/codestrata/telemetry/analytics/projection.py",
        ),
        ("engine/docs/telemetry-anonymous-analytics.md",),
        (
            "engine/tests/telemetry/test_analytics_contract.py",
            "engine/tests/telemetry/test_analytics_privacy.py",
        ),
        (),
    ),
    (
        "10.2",
        "Anonymous installation identity",
        (
            "engine/src/codestrata/telemetry/analytics/installation_identity.py",
            "engine/src/codestrata/telemetry/analytics/installation_identity_policy.py",
            "engine/src/codestrata/telemetry/analytics/installation_identity_storage.py",
        ),
        ("engine/docs/telemetry-installation-identity.md",),
        (
            "engine/tests/telemetry/test_installation_identity_lifecycle.py",
            "engine/tests/telemetry/test_installation_identity_privacy.py",
        ),
        (),
    ),
    (
        "10.3",
        "Runtime analytics",
        (
            "engine/src/codestrata/telemetry/analytics/runtime_analytics.py",
            "engine/src/codestrata/telemetry/analytics/runtime_analytics_projection.py",
        ),
        ("engine/docs/telemetry-runtime-analytics.md",),
        (
            "engine/tests/telemetry/test_runtime_analytics_privacy.py",
            "engine/tests/telemetry/test_runtime_analytics_collection.py",
        ),
        (),
    ),
    (
        "10.4",
        "Assessment analytics",
        (
            "engine/src/codestrata/telemetry/analytics/assessment_analytics.py",
            "engine/src/codestrata/telemetry/analytics/assessment_analytics_policy.py",
        ),
        ("engine/docs/telemetry-assessment-analytics.md",),
        ("engine/tests/telemetry/test_assessment_analytics_policy.py",),
        (),
    ),
    (
        "10.5",
        "Repository aggregate analytics",
        (
            "engine/src/codestrata/telemetry/analytics/repository_aggregate.py",
            "engine/src/codestrata/telemetry/analytics/repository_aggregate_policy.py",
        ),
        ("engine/docs/telemetry-repository-aggregate-analytics.md",),
        ("engine/tests/telemetry/test_repository_aggregate_policy.py",),
        (),
    ),
    (
        "10.6",
        "AI analytics",
        (
            "engine/src/codestrata/telemetry/analytics/ai_analytics.py",
            "engine/src/codestrata/telemetry/analytics/ai_analytics_policy.py",
            "engine/src/codestrata/telemetry/analytics/ai_analytics_catalogs.py",
        ),
        ("engine/docs/telemetry-ai-analytics.md",),
        ("engine/tests/telemetry/test_ai_analytics_policy.py",),
        (),
    ),
    (
        "10.7",
        "VS Code analytics",
        (
            "vscode-plugin/src/telemetry/analytics/runtimePolicy.ts",
            "vscode-plugin/src/telemetry/analytics/events.ts",
            "vscode-plugin/src/telemetry/analytics/unavailableSink.ts",
        ),
        ("vscode-plugin/docs/analytics.md",),
        ("vscode-plugin/src/test/analyticsRuntime.test.ts",),
        (),
    ),
    (
        "10.8",
        "Anonymous analytics privacy verification",
        ("verification/anonymous_analytics_privacy/runner.py",),
        ("verification/anonymous_analytics_privacy/README.md",),
        ("tests/verification/anonymous_analytics_privacy/test_integration.py",),
        ("verification/anonymous_analytics_privacy/contract.py",),
    ),
    (
        "10.9",
        "Epic boundary and completion verification",
        ("verification/anonymous_analytics_completion/runner.py",),
        ("verification/anonymous_analytics_completion/README.md",),
        ("tests/verification/anonymous_analytics_completion/test_integration.py",),
        ("verification/anonymous_analytics_completion/contract.py",),
    ),
)


def build_slice_matrix(
    monorepo: Path,
) -> tuple[list[SliceEvidence], list[CheckResult], list[Defect]]:
    matrix: list[SliceEvidence] = []
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for slice_id, purpose, impl, docs, tests, verification in _SLICES:
        missing_impl = [p for p in impl if not (monorepo / p).is_file()]
        missing_docs = [p for p in docs if not (monorepo / p).is_file()]
        missing_tests = [p for p in tests if not (monorepo / p).is_file()]
        missing_ver = [p for p in verification if not (monorepo / p).is_file()]
        ok = not (missing_impl or missing_docs or missing_tests or missing_ver)
        status = "complete" if ok else "incomplete"
        matrix.append(
            SliceEvidence(
                slice_id=slice_id,
                purpose=purpose,
                implementation_evidence=",".join(impl),
                documentation_evidence=",".join(docs),
                test_evidence=",".join(tests),
                verification_evidence=",".join(verification) if verification else "n/a",
                status=status,
            )
        )
        checks.append(
            CheckResult(
                name=f"slice:{slice_id}:evidence",
                ok=ok,
                detail=(
                    f"missing_impl={missing_impl};missing_docs={missing_docs};"
                    f"missing_tests={missing_tests};missing_ver={missing_ver}"
                    if not ok
                    else "present"
                ),
                category="slices",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "missing slice evidence",
                    slice_id,
                    "all evidence present",
                    "incomplete",
                    detail=checks[-1].detail,
                )
            )

    checks.append(
        CheckResult(
            name="slice:count_9",
            ok=len(matrix) == 9 and all(s.status == "complete" for s in matrix),
            detail=str(sum(1 for s in matrix if s.status == "complete")),
            category="slices",
        )
    )
    return matrix, checks, defects
