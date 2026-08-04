"""Engine version alignment tests for SV.16."""

from __future__ import annotations

import re
from pathlib import Path

from verification.release_artifacts.contract import INTENDED_RELEASE_VERSION, monorepo_root_from_here
from verification.release_artifacts.versions import check_versions, read_versions

_VERSION_RE = re.compile(r'^\s*version\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def _engine_version_from_pyproject(monorepo: Path) -> str | None:
    text = (monorepo / "engine" / "pyproject.toml").read_text(encoding="utf-8")
    match = _VERSION_RE.search(text)
    return match.group(1) if match else None


def test_intended_release_version_constant() -> None:
    assert INTENDED_RELEASE_VERSION == "0.2.0"


def test_engine_pyproject_version_readable() -> None:
    monorepo = monorepo_root_from_here()
    engine_version = _engine_version_from_pyproject(monorepo)
    assert engine_version is not None


def test_release_gate_engine_version_matches_intended() -> None:
    monorepo = monorepo_root_from_here()
    engine_version = _engine_version_from_pyproject(monorepo)
    assert engine_version == INTENDED_RELEASE_VERSION


def test_check_versions_detects_engine_alignment() -> None:
    monorepo = monorepo_root_from_here()
    versions = read_versions(monorepo)
    assert "engine" in versions
    checks, defects, _warnings = check_versions(monorepo)
    engine_check = next(c for c in checks if c.name == "versions:engine_matches_intended")
    if versions["engine"] == INTENDED_RELEASE_VERSION:
        assert engine_check.ok is True
        assert not any(d.component == "engine/pyproject.toml" for d in defects)
    else:
        assert engine_check.ok is False
        assert any(d.component == "engine/pyproject.toml" for d in defects)
