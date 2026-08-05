"""SV.9 packaging / architecture boundary tests."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PLATFORM = REPO / "platform"
PKG = PLATFORM / "src" / "codestrata_platform"
VERIFICATION = PLATFORM / "verification" / "community_data_lake"
ENGINE = REPO / "engine" / "src" / "codestrata"


def test_verification_outside_runtime_package() -> None:
    assert (VERIFICATION / "runner.py").is_file()
    assert (VERIFICATION / "README.md").is_file()
    assert not (PKG / "verification").exists()


def test_engine_does_not_import_data_lake_verification() -> None:
    hits = []
    for path in ENGINE.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "verification.community_data_lake" in text:
            hits.append(str(path.relative_to(ENGINE)))
    assert not hits, hits
