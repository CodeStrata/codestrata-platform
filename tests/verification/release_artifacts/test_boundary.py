"""Wheel/platform/infrastructure boundary tests."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from verification.release_artifacts.contract import monorepo_root_from_here
from verification.release_artifacts.platform_boundary import check_platform_boundary
from verification.release_artifacts.wheel import inspect_wheel


def _make_wheel(tmp_path: Path, members: dict[str, str]) -> Path:
    wheel = tmp_path / "test-0.2.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr(
            "codestrata-0.2.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: codestrata\nVersion: 0.2.0\nLicense: MIT\n",
        )
        archive.writestr(
            "codestrata-0.2.0.dist-info/entry_points.txt",
            "[console_scripts]\ncodestrata = codestrata.cli.main:main\n",
        )
        for name, content in members.items():
            archive.writestr(name, content)
    return wheel


def test_wheel_forbids_platform_paths(tmp_path: Path) -> None:
    wheel = _make_wheel(
        tmp_path,
        {
            "codestrata/__init__.py": "",
            "platform/src/leak.py": "x",
        },
    )
    checks, defects = inspect_wheel(wheel)
    assert any(not c.ok for c in checks if "forbidden_paths" in c.name)
    assert defects


def test_wheel_requires_codestrata_package(tmp_path: Path) -> None:
    wheel = _make_wheel(tmp_path, {"otherpkg/__init__.py": ""})
    _checks, defects = inspect_wheel(wheel)
    assert any(d.classification == "missing_package" for d in defects)


def test_platform_boundary_detects_codestrata_platform(tmp_path: Path) -> None:
    wheel = _make_wheel(
        tmp_path,
        {
            "codestrata/__init__.py": "",
            "codestrata_platform/__init__.py": "",
        },
    )
    monorepo = monorepo_root_from_here()
    artifact_dir = monorepo / "reports/verification/sv16/test-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    target = artifact_dir / wheel.name
    target.write_bytes(wheel.read_bytes())
    rel = str(target.relative_to(monorepo))
    checks, defects = check_platform_boundary(
        monorepo,
        wheel_relative=rel,
        sdist_relative=None,
    )
    assert any(not c.ok for c in checks)
    assert defects
