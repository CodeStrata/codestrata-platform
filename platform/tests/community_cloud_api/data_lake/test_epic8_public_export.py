"""Epic 8 public export boundary tests (Slice 8.15)."""

from __future__ import annotations

import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_public_export_excludes_platform_and_infrastructure() -> None:
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden
    assert "infrastructure/" in forbidden
