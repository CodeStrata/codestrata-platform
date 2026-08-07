"""Minimal Slice 12.8 package presence test."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_export_repository_router_exists() -> None:
    assert (ROOT / "scripts/export_repository.py").is_file()
    assert (ROOT / "scripts/repository_export_router").is_dir()
    assert (ROOT / "verification/repository_export_targets/contract.py").is_file()
