"""Privacy, events, catalog, preview, transport, isolation."""

from __future__ import annotations

from verification.privacy_first_telemetry.catalogs import check_catalogs
from verification.privacy_first_telemetry.contract import monorepo_root_from_here
from verification.privacy_first_telemetry.engine_inputs import load_engine_inventory
from verification.privacy_first_telemetry.events import check_events
from verification.privacy_first_telemetry.isolation import check_isolation
from verification.privacy_first_telemetry.preview import check_preview
from verification.privacy_first_telemetry.privacy import check_privacy
from verification.privacy_first_telemetry.transport import check_transport
from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory


def test_privacy_matrix() -> None:
    vscode = load_vscode_inventory(monorepo_root_from_here())
    checks, defects = check_privacy(vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_events_and_fields() -> None:
    root = monorepo_root_from_here()
    engine = load_engine_inventory()
    vscode = load_vscode_inventory(root)
    checks, defects, notes = check_events(engine, vscode)
    assert notes
    assert not defects
    assert all(c.ok for c in checks)


def test_catalogs() -> None:
    root = monorepo_root_from_here()
    vscode = load_vscode_inventory(root)
    checks, defects = check_catalogs(root, vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_preview() -> None:
    vscode = load_vscode_inventory(monorepo_root_from_here())
    checks, defects = check_preview(vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_transport() -> None:
    vscode = load_vscode_inventory(monorepo_root_from_here())
    checks, defects = check_transport(vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_isolation() -> None:
    vscode = load_vscode_inventory(monorepo_root_from_here())
    checks, defects = check_isolation(vscode)
    assert not defects
    assert all(c.ok for c in checks)
