"""Version consistency checks across distributable metadata."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _read_python_version(pyproject: Path) -> str | None:
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        import tomli as tomllib  # type: ignore

    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return (data.get("project") or {}).get("version")


def _read_node_version(package_json: Path) -> str | None:
    data = json.loads(package_json.read_text(encoding="utf-8"))
    value = data.get("version")
    return str(value) if value is not None else None


def _cli_version(root: Path) -> str | None:
    init_path = root / "engine" / "src" / "codestrata" / "__init__.py"
    if not init_path.is_file():
        return None
    text = init_path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
    if match:
        return match.group(1)
    # Fallback: many packages expose version only via package metadata.
    return _read_python_version(root / "engine" / "pyproject.toml")


def check_version_consistency(root: Path = ROOT) -> dict[str, Any]:
    versions: dict[str, str | None] = {
        "engine_pyproject": _read_python_version(root / "engine" / "pyproject.toml"),
        "engine_cli": _cli_version(root),
        "vscode_extension": _read_node_version(root / "vscode-plugin" / "package.json"),
        "cursor_extension": _read_node_version(root / "cursor-plugin" / "package.json"),
        "docs_site": _read_node_version(root / "docs" / "package.json")
        if (root / "docs" / "package.json").is_file()
        else None,
    }
    issues: list[str] = []
    engine = versions.get("engine_pyproject")
    cli = versions.get("engine_cli")
    if engine and cli and engine != cli:
        issues.append(f"Engine package version {engine} != CLI/module version {cli}")
    # Extensions may intentionally differ from Engine; only flag missing.
    for key in ("vscode_extension", "cursor_extension"):
        if not versions.get(key):
            issues.append(f"missing version for {key}")
    if not engine:
        issues.append("missing engine pyproject version")
    return {
        "versions": versions,
        "issues": issues,
        "passed": len(issues) == 0,
        "notes": [
            "Extension versions may differ from Engine package version.",
            "Schema versions are independent of product release versions.",
        ],
    }
