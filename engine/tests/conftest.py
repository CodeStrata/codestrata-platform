"""Pytest path helpers for the Community Engine test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

ENGINE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ENGINE_ROOT.parent
EXAMPLES_ROOT = (
    REPO_ROOT / "examples"
    if (REPO_ROOT / "examples").is_dir()
    else ENGINE_ROOT / "examples"
)


@pytest.fixture(scope="session")
def engine_root() -> Path:
    return ENGINE_ROOT


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def examples_root() -> Path:
    return EXAMPLES_ROOT
