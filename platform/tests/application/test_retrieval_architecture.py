"""Architecture guarantees for Engineering Retrieval indexing."""

from __future__ import annotations

import ast
from pathlib import Path

RETRIEVAL_DOMAIN = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "domain"
    / "retrieval"
)
RETRIEVAL_APPLICATION = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "application"
    / "retrieval"
)
RETRIEVAL_API = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "api"
    / "retrieval"
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


def test_retrieval_domain_has_no_infrastructure_imports() -> None:
    for path in sorted(RETRIEVAL_DOMAIN.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module
            assert not module.startswith("codestrata_platform.api")
            assert not module.startswith("codestrata_platform.rag")


def test_retrieval_application_has_no_sqlalchemy_or_llm() -> None:
    for path in sorted(RETRIEVAL_APPLICATION.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in source
        assert "openai" not in source.lower() or "EmbeddingModelId" in source
        assert "anthropic" not in source.lower()
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert not module.startswith("codestrata_platform.rag")
            assert not module.startswith("codestrata_engine")


def test_retrieval_api_calls_application_only() -> None:
    for path in sorted(RETRIEVAL_API.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module


def test_chunk_builder_consumes_platform_intelligence_only() -> None:
    chunking = RETRIEVAL_APPLICATION / "chunking.py"
    modules = _imported_modules(chunking)
    assert any(module.startswith("codestrata_platform.domain.engineering") for module in modules)
    assert any(
        module.startswith("codestrata_platform.domain.knowledge_graph") for module in modules
    )
    forbidden_prefixes = (
        "codestrata_platform.domain.artifact",
        "codestrata_platform.rag",
        "codestrata_engine",
    )
    for module in modules:
        assert not any(module.startswith(prefix) for prefix in forbidden_prefixes)
