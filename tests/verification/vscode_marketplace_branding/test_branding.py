"""Unit tests for Slice 13.12 Marketplace branding verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_marketplace_branding.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.vscode_marketplace_branding.inventory import asset_inventory_stable
from verification.vscode_marketplace_branding.runner import build_report, write_report


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert "file://" not in text


def test_runner_deterministic() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    inv_a = asset_inventory_stable(monorepo)
    inv_b = asset_inventory_stable(monorepo)
    assert inv_a == inv_b


def test_negative_forbidden_claim_detection() -> None:
    from verification.vscode_marketplace_branding.contract import (
        FORBIDDEN_CLAIM_FRAGMENTS,
    )

    assert "supports cursor" in FORBIDDEN_CLAIM_FRAGMENTS
    assert "all source always stays local" in FORBIDDEN_CLAIM_FRAGMENTS
