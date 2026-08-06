"""Consent / persistence / identity matrices."""

from __future__ import annotations

from verification.privacy_first_telemetry.consent import check_consent
from verification.privacy_first_telemetry.contract import monorepo_root_from_here
from verification.privacy_first_telemetry.engine_inputs import load_engine_inventory
from verification.privacy_first_telemetry.identity import check_identity
from verification.privacy_first_telemetry.persistence import check_persistence
from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory


def test_consent_matrix() -> None:
    vscode = load_vscode_inventory(monorepo_root_from_here())
    checks, defects = check_consent(vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_persistence_matrix() -> None:
    root = monorepo_root_from_here()
    vscode = load_vscode_inventory(root)
    checks, defects = check_persistence(root, vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_identity_matrix() -> None:
    root = monorepo_root_from_here()
    engine = load_engine_inventory()
    vscode = load_vscode_inventory(root)
    checks, defects = check_identity(engine, vscode)
    assert not defects
    assert all(c.ok for c in checks)
