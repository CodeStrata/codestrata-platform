"""Smoke tests for Slice 17.26 Community public documentation reconciliation."""

from __future__ import annotations

import json

from verification.community_public_documentation_reconciliation.contract import (
    CONTRACT_RELATIVE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SUITE_ID,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_public_documentation_reconciliation.determinism import (
    reports_byte_identical,
)
from verification.community_public_documentation_reconciliation.helpers import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_public_documentation_reconciliation.runner import (
    build_report,
    write_report,
)


def test_contract_boundary() -> None:
    c = default_contract()
    assert c.start_slice_17_26 is True
    assert c.start_slice_17_27 is False
    assert SCHEMA_NAME == "community-public-documentation-reconciliation-verification"
    assert SCHEMA_VERSION == "1.0.0"
    assert SUITE_ID == "sv17-26"
    assert POLICY_REQUIRED_VALUES["start_slice_17_26"] is True
    assert POLICY_REQUIRED_VALUES["start_slice_17_27"] is False
    assert POLICY_REQUIRED_VALUES["no_cli_publish"] is True
    assert POLICY_REQUIRED_VALUES["no_vscode_marketplace_publish"] is True
    assert POLICY_REQUIRED_VALUES["no_release_tag"] is True
    assert POLICY_REQUIRED_VALUES["no_full_22_repository_release_corpus"] is True


def test_policy_and_contract_files() -> None:
    root = monorepo_root_from_here()
    policy = json.loads((root / POLICY_RELATIVE).read_text(encoding="utf-8"))
    for key, expected in POLICY_REQUIRED_VALUES.items():
        assert policy.get(key) == expected, key
    contract = json.loads((root / CONTRACT_RELATIVE).read_text(encoding="utf-8"))
    assert contract.get("$id", "").startswith(SCHEMA_NAME) or contract.get("title")
    # 17.25 fence remains intact on its own policy.
    status_policy = json.loads(
        (
            root / "platform/policies/community_status_github_authority_policy.json"
        ).read_text(encoding="utf-8")
    )
    assert status_policy.get("start_slice_17_26") is False


def test_build_report_smoke() -> None:
    root = monorepo_root_from_here()
    report = build_report(root)
    assert report.schema == SCHEMA_NAME
    assert report.slice == "17.26"
    assert report.suite_id == SUITE_ID
    assert report.epic17_boundary["start_slice_17_26"] is True
    assert report.epic17_boundary["start_slice_17_27"] is False
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS", "FAIL"}
    text = dict_to_canonical_json(report.to_dict())
    assert "/Users/" not in text
    assert "timestamp" not in text
    assert report_text_is_safe(text)


def test_determinism_and_write() -> None:
    root = monorepo_root_from_here()
    r1 = build_report(root)
    r2 = build_report(root)
    assert reports_byte_identical(r1.to_dict(), r2.to_dict())
    path = write_report(root, r2)
    assert path.name == "community-public-documentation-reconciliation-verification.json"
    assert "sv17-26" in path.as_posix()
    text = path.read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert report_text_is_safe(text)


def test_runner_import() -> None:
    from verification.community_public_documentation_reconciliation.runner import main

    assert callable(main)
