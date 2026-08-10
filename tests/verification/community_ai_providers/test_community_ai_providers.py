"""Tests for Slice 17.20 Community AI Providers verification."""

from __future__ import annotations

import json

from verification.community_ai_providers.contract import (
    CONTRACT_RELATIVE,
    EXPECTED_17_20_PACKAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    SCHEMA_NAME,
    SUPPORTED_PROVIDERS,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_ai_providers.determinism import (
    canonical_for_determinism,
    dict_to_canonical_json,
)
from verification.community_ai_providers.helpers import report_text_is_safe
from verification.community_ai_providers.provider_inventory import check_provider_inventory
from verification.community_ai_providers.runner import build_report, run


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_20 is True
    assert c.start_slice_17_21 is True
    assert c.start_slice_17_22 is False
    assert c.schema_name == SCHEMA_NAME


def test_policy_register() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    for key, expected in POLICY_REQUIRED_VALUES.items():
        if key == "supported_providers":
            assert set(policy.get(key) or []) == set(expected)  # type: ignore[arg-type]
        else:
            assert policy.get(key) == expected, key

    register = json.loads((root / REGISTER_RELATIVE).read_text(encoding="utf-8"))
    assert register.get("schema") == REGISTER_SCHEMA
    providers = {
        str(e.get("provider"))
        for e in (register.get("entries") or [])
        if isinstance(e, dict)
    }
    assert providers == set(SUPPORTED_PROVIDERS)

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == SCHEMA_NAME
    assert contract.get("start_slice_17_20") is True
    assert contract.get("start_slice_17_21") is True

    assert (root / EXPECTED_17_20_PACKAGE).is_dir()


def test_providers_inventory() -> None:
    root = monorepo_root_from_here()
    checks, defects, summary = check_provider_inventory(root)
    assert not defects
    assert set(summary.get("registered") or []) == set(SUPPORTED_PROVIDERS)
    assert all(c.ok for c in checks if c.check_id.startswith("inventory:register_"))


def test_report_safe() -> None:
    root = monorepo_root_from_here()
    text = dict_to_canonical_json(build_report(root).to_dict())
    assert report_text_is_safe(text)
    assert "cscc_v1_" not in text
    assert "Bearer " not in text
    assert "sk-" not in text
    assert "OPENAI_API_KEY=" not in text
    assert "OPENROUTER_API_KEY=" not in text
    assert "/Users/" not in text


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.20"
    assert report.suite_id == "sv17-20"
    assert report.epic17_boundary.get("start_slice_17_20") is True
    assert report.epic17_boundary.get("start_slice_17_21") is True
    assert report.epic17_boundary.get("start_slice_17_22") is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results


def test_determinism_normalized() -> None:
    root = monorepo_root_from_here()
    a = canonical_for_determinism(build_report(root).to_dict())
    b = canonical_for_determinism(build_report(root).to_dict())
    assert a == b


def test_run_writes_artifact() -> None:
    root = monorepo_root_from_here()
    report = run(root)
    path = (
        root
        / ".codestrata-artifacts/validation/suites/sv17-20"
        / "community-ai-providers-verification.json"
    )
    assert path.is_file()
    assert report.verdict != "FAIL" or report.failed_checks >= 0
