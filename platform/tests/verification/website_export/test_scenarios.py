"""Scenario and demo regression checks."""

from __future__ import annotations

from pathlib import Path

from verification.website_export.scenarios import (
    check_anonymized_scope,
    check_identity_alias_stability,
    check_oss_demonstration_regression,
    check_policy_token_required,
    check_unsafe_text_rejection,
    check_writer_partial_failure_contract,
)


def test_scenarios(verified_export, tmp_path: Path) -> None:
    results = (
        check_identity_alias_stability(verified_export)
        + check_anonymized_scope(verified_export)
        + check_unsafe_text_rejection()
        + check_policy_token_required(verified_export)
        + check_oss_demonstration_regression()
        + check_writer_partial_failure_contract(tmp_path, verified_export)
    )
    assert all(item.ok for item in results), [r for r in results if not r.ok]
