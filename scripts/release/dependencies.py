"""Dependency inventory for distributable components."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _parse_python_deps(pyproject: Path) -> dict[str, Any]:
    text = pyproject.read_text(encoding="utf-8")
    # Lightweight parse — avoid requiring tomllib edge cases for optional extras.
    try:
        import tomllib
    except ImportError:  # pragma: no cover
        import tomli as tomllib  # type: ignore

    data = tomllib.loads(text)
    project = data.get("project") or {}
    optional = project.get("optional-dependencies") or {}
    return {
        "name": project.get("name"),
        "version": project.get("version"),
        "requires_python": project.get("requires-python"),
        "direct": list(project.get("dependencies") or []),
        "optional": {key: list(value) for key, value in optional.items()},
        "has_path_dependency": any(
            " @ file:" in dep or "path =" in dep for dep in project.get("dependencies") or []
        ),
        "has_git_dependency": any(
            " @ git+" in dep or "git+" in dep for dep in project.get("dependencies") or []
        ),
    }


def _parse_node_deps(package_json: Path) -> dict[str, Any]:
    data = json.loads(package_json.read_text(encoding="utf-8"))
    lock = package_json.parent / "package-lock.json"
    return {
        "name": data.get("name"),
        "version": data.get("version"),
        "dependencies": data.get("dependencies") or {},
        "devDependencies": data.get("devDependencies") or {},
        "optionalDependencies": data.get("optionalDependencies") or {},
        "lockfile_present": lock.is_file(),
        "has_file_protocol": any(
            str(v).startswith("file:")
            for v in {
                **(data.get("dependencies") or {}),
                **(data.get("devDependencies") or {}),
            }.values()
        ),
        "has_git_protocol": any(
            str(v).startswith(("git+", "github:"))
            for v in {
                **(data.get("dependencies") or {}),
                **(data.get("devDependencies") or {}),
            }.values()
        ),
    }


def build_dependency_inventory(root: Path = ROOT) -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    engine = root / "engine" / "pyproject.toml"
    if engine.is_file():
        components.append(
            {
                "component": "codestrata-engine",
                "ecosystem": "python",
                "path": "engine/pyproject.toml",
                **_parse_python_deps(engine),
            }
        )
    for name, rel in (
        ("codestrata-vscode", "vscode-plugin/package.json"),
        ("codestrata-cursor", "cursor-plugin/package.json"),
        ("codestrata-docs", "docs/package.json"),
    ):
        path = root / rel
        if path.is_file():
            components.append(
                {
                    "component": name,
                    "ecosystem": "node",
                    "path": rel,
                    **_parse_node_deps(path),
                }
            )

    issues: list[str] = []
    for item in components:
        if item.get("has_path_dependency") or item.get("has_file_protocol"):
            issues.append(f"{item['component']}: local path dependency detected")
        if item.get("has_git_dependency") or item.get("has_git_protocol"):
            issues.append(f"{item['component']}: git dependency detected")
        if item.get("ecosystem") == "node" and not item.get("lockfile_present"):
            issues.append(f"{item['component']}: package-lock.json missing")
        # Bounded versions: warn on bare unpinned python deps without operators
        if item.get("ecosystem") == "python":
            for dep in item.get("direct") or []:
                if isinstance(dep, str) and not re.search(r"[<>=!~]", dep):
                    issues.append(f"{item['component']}: unbounded dependency {dep!r}")

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "components": components,
        "issues": issues,
        "passed": len(issues) == 0,
        "upgrade_recommendations": [
            "Review unbounded or loosely pinned dependencies before public release.",
            "Do not upgrade packages in Phase 14.2 unless release-blocking.",
        ],
    }


def write_dependency_inventory(destination: Path, root: Path = ROOT) -> Path:
    payload = build_dependency_inventory(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
