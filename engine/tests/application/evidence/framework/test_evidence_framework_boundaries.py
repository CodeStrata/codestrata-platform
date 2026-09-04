from __future__ import annotations

import ast
from pathlib import Path


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_collection_assessment_and_reporting_are_dependency_isolated() -> None:
    source = Path(__file__).parents[4] / "src" / "codestrata"
    collectors = _imports(source / "application" / "evidence" / "framework" / "collectors.py")
    assessment = _imports(source / "application" / "evidence" / "framework" / "assessment.py")
    renderer = _imports(source / "reporting" / "evidence_framework" / "renderer.py")
    assert not any("assessment" in item or "reporting" in item for item in collectors)
    assert not any("collectors" in item or "reporting" in item for item in assessment)
    assert not any("collectors" in item or "application.evidence" in item for item in renderer)
