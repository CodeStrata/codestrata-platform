"""Architecture guarantees for Strategic Portfolio Roadmap."""

from __future__ import annotations

import ast
from pathlib import Path

ROADMAP_APPLICATION = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "application"
    / "strategic_roadmap"
)
ROADMAP_API = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "api"
    / "strategic_roadmap"
)

_FORBIDDEN_PREFIXES = (
    "codestrata_platform.infrastructure",
    "codestrata_platform.domain.engineering",
    "codestrata_platform.domain.knowledge_graph",
    "codestrata_platform.domain.retrieval",
    "codestrata_platform.domain.answering",
    "codestrata_platform.application.knowledge_graph",
    "codestrata_platform.application.retrieval",
    "codestrata_platform.application.answering",
    "codestrata_platform.application.portfolio_retrieval",
    "codestrata_platform.application.portfolio_answering",
    "codestrata_platform.application.portfolio",
    "codestrata_platform.application.executive_intelligence.aggregation",
    "codestrata_platform.application.executive_presentation",
    "codestrata_platform.rag",
    "codestrata_engine",
    "openai",
    "anthropic",
    "boto3",
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


def test_roadmap_application_forbids_disallowed_imports() -> None:
    for path in sorted(ROADMAP_APPLICATION.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in source
        assert "openai" not in source
        for module in _imported_modules(path):
            assert not any(
                module.startswith(prefix) for prefix in _FORBIDDEN_PREFIXES
            ), f"{path.name} imports forbidden module {module}"


def test_roadmap_builder_consumes_executive_intelligence_only() -> None:
    builder = ROADMAP_APPLICATION / "builder.py"
    modules = _imported_modules(builder)
    assert any(
        module.startswith("codestrata_platform.application.executive_intelligence")
        or module.startswith("codestrata_platform.domain.executive_intelligence")
        for module in modules
    )
    for module in modules:
        assert not module.startswith("codestrata_platform.domain.portfolio")
        assert not module.startswith("codestrata_platform.application.portfolio")
        assert not module.startswith(
            "codestrata_platform.application.executive_intelligence.aggregation"
        )


def test_roadmap_api_calls_application_only() -> None:
    for path in sorted(ROADMAP_API.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module
            assert not any(
                module.startswith(prefix) for prefix in _FORBIDDEN_PREFIXES
            ), f"{path.name} imports forbidden module {module}"
