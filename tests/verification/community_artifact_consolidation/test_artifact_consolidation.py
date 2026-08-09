"""Tests for Slice 17.12 verification package."""

from __future__ import annotations

from pathlib import Path

from verification.community_artifact_consolidation.contract import default_contract
from verification.community_artifact_consolidation.determinism import dict_to_canonical_json
from verification.community_artifact_consolidation.runner import build_report


def test_contract_defaults() -> None:
    c = default_contract()
    assert c.start_slice_17_12 is True
    assert c.start_slice_17_13 is False


def test_build_report_deterministic(monorepo_root: Path | None = None) -> None:
    root = Path(__file__).resolve().parents[3]
    r1 = build_report(root)
    r2 = build_report(root)
    assert dict_to_canonical_json(r1.to_dict()) == dict_to_canonical_json(r2.to_dict())
    assert r1.failed_checks == 0
    assert r1.epic17_boundary.get("start_slice_17_13") is False
