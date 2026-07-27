"""Architecture guarantees for Engineering Knowledge Graph projection."""

from __future__ import annotations

import ast
from pathlib import Path

KG_DOMAIN = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "domain"
    / "knowledge_graph"
)
KG_APPLICATION = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "application"
    / "knowledge_graph"
)
KG_API = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "api"
    / "knowledge_graph"
)


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_graph_domain_has_no_infrastructure_imports() -> None:
    for path in sorted(KG_DOMAIN.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module
            assert not module.startswith("codestrata_platform.api")


def test_graph_application_has_no_sqlalchemy() -> None:
    for path in sorted(KG_APPLICATION.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in source
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")


def test_graph_api_calls_application_only() -> None:
    for path in sorted(KG_API.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module


def test_projector_consumes_engineering_snapshot_only() -> None:
    projection = KG_APPLICATION / "projection.py"
    modules = _imported_modules(projection)
    assert any(module.startswith("codestrata_platform.domain.engineering") for module in modules)
    forbidden_prefixes = (
        "codestrata_platform.application.intelligence",
        "codestrata_platform.domain.artifact",
        "codestrata_platform.domain.intelligence",
        "codestrata_engine",
        "codestrata_platform.rag",
    )
    for module in modules:
        assert not any(module.startswith(prefix) for prefix in forbidden_prefixes)
