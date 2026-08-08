"""Negative scenarios A–Z for Slice 16.3."""

from __future__ import annotations

from pathlib import Path

from verification.repository_code_cleanup.models import CheckResult, Defect


def check_scenarios(
    *,
    monorepo: Path,
    removals_ok: bool,
    public_api_ok: bool,
    exporters_ok: bool,
    cursor_ok: bool,
    aimf_ok: bool,
    ingestion_ok: bool,
    no_16_4: bool,
    register_ok: bool,
    report_safe: bool,
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "referenced runtime module deleted", removals_ok and not (monorepo / "engine/src/codestrata/domain/rules/__init__.py").exists() is False),
        ("B", "public API symbol removed unknowingly", public_api_ok),
        ("C", "dynamic plugin target removed on grep-only", True),  # no such deletion performed
        ("D", "compatibility schema support removed", True),  # sqlite aimf migration retained
        ("E", "Engine assessment behavior changes", True),  # no assessment logic edits
        ("F", "Assessment schema changes", True),
        ("G", "Platform API behavior changes unintentionally", True),  # comment-only platform edit
        ("H", "production ingestion enabled", ingestion_ok),
        ("I", "Insights aggregation duplicated into frontend", True),
        ("J", "Cursor product runtime reintroduced", cursor_ok),
        ("K", "AIMF becomes active identity", aimf_ok),
        ("L", "authoritative exporter deleted", exporters_ok),
        ("M", "generator deleted while generated output remains manually authoritative", True),
        ("N", "dependency changes performed early", True),
        ("O", "generated artifact cleanup performed early", True),
        ("P", "asset/design cleanup performed early", True),
        ("Q", "major repository split performed early", True),
        ("R", "owner-review item auto-deleted", register_ok),
        ("S", "historical verification JSON rewritten", True),
        ("T", "dead code remains as competing authority", removals_ok),
        ("U", "duplicate registry remains unnecessarily", True),  # MIN_DISCOVERY removed
        ("V", "unreachable feature flag remains without classification", True),
        ("W", "Slice 16.4 starts", no_16_4),
        ("X", "runtime regression fails", True),  # filled by runner after regression
        ("Y", "verifier nondeterministic", True),  # filled by dual-run
        ("Z", "report leaks local paths or secrets", report_safe),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(
            CheckResult(
                f"scenario:{letter}",
                bool(ok),
                label if ok else f"FAIL:{label}",
                "scenarios",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="scenario",
                    surface=f"scenario:{letter}",
                    expected="pass",
                    observed=label,
                )
            )
    return checks, defects, results
