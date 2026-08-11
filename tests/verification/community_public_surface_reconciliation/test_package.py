"""Smoke tests for Slice 18.6 Public Surface Reconciliation."""

from __future__ import annotations

import json

from verification.community_public_surface_reconciliation.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_public_surface_reconciliation.determinism import (
    reports_byte_identical,
)
from verification.community_public_surface_reconciliation.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_public_surface_reconciliation.runner import (
    build_report,
    write_report,
)


def test_contract_boundary() -> None:
    c = default_contract()
    assert c.start_slice_18_6 is True
    assert c.start_slice_18_7 is False
    assert SCHEMA_NAME == "community-public-surface-reconciliation-verification"
    assert SCHEMA_VERSION == "1.0.0"
    assert SUITE_ID == "sv18-6"
    assert POLICY_REQUIRED_VALUES["start_slice_18_7"] is False


def test_policy_and_contract_files() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, key
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert "community-public-surface-reconciliation-verification" in contract.get(
        "$id", ""
    )


def test_build_report_smoke() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "18.6"
    assert report.suite_id == SUITE_ID
    assert report.epic18_boundary["start_slice_18_6"] is True
    assert report.epic18_boundary["start_slice_18_7"] is False
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "timestamp" not in text
    assert report_text_is_safe(text)
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}


def test_determinism_and_write() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
    path = write_report(root, r2)
    assert path.name == "community-public-surface-reconciliation-verification.json"
    assert "sv18-6" in path.as_posix()


def test_runner_import() -> None:
    from verification.community_public_surface_reconciliation.runner import main

    assert callable(main)
