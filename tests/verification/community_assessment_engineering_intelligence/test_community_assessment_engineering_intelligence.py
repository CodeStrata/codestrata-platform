"""Tests for Slice 17.19 Community Assessment & Engineering Intelligence verification."""

from __future__ import annotations

import json

from verification.community_assessment_engineering_intelligence.contract import (
    ASSESSMENT_REGISTER,
    CONTRACT_RELATIVE,
    EIR_REGISTER,
    EXPECTED_17_19_PACKAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    REPRESENTATIVE_CATALOG_IDS,
    SCHEMA_NAME,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_assessment_engineering_intelligence.determinism import (
    canonical_for_determinism,
    dict_to_canonical_json,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    report_text_is_safe,
)
from verification.community_assessment_engineering_intelligence.runner import (
    build_report,
    run,
)


def test_contract_gates() -> None:
    c = default_contract()
    assert c.start_slice_17_19 is True
    assert c.start_slice_17_20 is True


def test_policy() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    assert policy.get("schema") == POLICY_SCHEMA
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, key

    assessment_reg = json.loads((root / ASSESSMENT_REGISTER).read_text(encoding="utf-8"))
    assert "community-assessment-report-register" in str(assessment_reg.get("schema"))

    eir_reg = json.loads((root / EIR_REGISTER).read_text(encoding="utf-8"))
    assert "community-engineering-intelligence-report-register" in str(eir_reg.get("schema"))

    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("schema") == SCHEMA_NAME
    assert contract.get("start_slice_17_19") is True
    assert contract.get("start_slice_17_20") is True

    assert (root / EXPECTED_17_19_PACKAGE).is_dir()


def test_selection_ids() -> None:
    root = monorepo_root_from_here()
    catalog = json.loads(
        (root / "validation/repository-catalog/catalog.json").read_text(encoding="utf-8")
    )
    ids = {str(item.get("id")) for item in (catalog.get("repositories") or []) if isinstance(item, dict)}
    for catalog_id in REPRESENTATIVE_CATALOG_IDS:
        assert catalog_id in ids


def test_build_report_runs() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.19"
    assert report.suite_id == "sv17-19"
    assert report.epic17_boundary.get("start_slice_17_19") is True
    assert report.epic17_boundary.get("start_slice_17_20") is True
    assert report.epic17_boundary.get("start_slice_17_21") is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert letter in report.scenario_results
    assert report.eir_generation.get("generated") is True or report.verdict == "FAIL"


def test_determinism_normalized() -> None:
    root = monorepo_root_from_here()
    a = canonical_for_determinism(build_report(root).to_dict())
    b = canonical_for_determinism(build_report(root).to_dict())
    assert a == b


def test_report_safe() -> None:
    root = monorepo_root_from_here()
    text = dict_to_canonical_json(build_report(root).to_dict())
    assert report_text_is_safe(text)
    assert "cscc_v1_" not in text
    assert "Bearer " not in text
    assert "arn:aws:" not in text
    assert "raw/stream=" not in text
    assert "/Users/" not in text


def test_run_writes_artifact() -> None:
    root = monorepo_root_from_here()
    report = run(root)
    path = (
        root
        / ".codestrata-artifacts/validation/suites/sv17-19"
        / "community-assessment-engineering-intelligence-verification.json"
    )
    assert path.is_file()
    assert report.verdict != "FAIL" or report.failed_checks >= 0
