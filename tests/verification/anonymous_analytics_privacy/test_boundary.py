"""Boundary tests for Slice 10.8 verification package."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_privacy.boundaries import check_boundaries
from verification.anonymous_analytics_privacy.contract import monorepo_root_from_here
from verification.anonymous_analytics_privacy.vscode_inputs import (
    load_vscode_analytics_inventory,
)


def test_boundaries() -> None:
    root = monorepo_root_from_here()
    vscode = load_vscode_analytics_inventory(root)
    checks, defects = check_boundaries(root, vscode)
    assert not defects
    assert all(c.ok for c in checks)


def test_verification_package_has_no_network_imports() -> None:
    root = (
        monorepo_root_from_here() / "verification" / "anonymous_analytics_privacy"
    )
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "import urllib" not in text
        assert "import requests" not in text
        assert "import boto3" not in text
        assert "from boto3" not in text
        assert "import socket" not in text
        assert "from socket" not in text
