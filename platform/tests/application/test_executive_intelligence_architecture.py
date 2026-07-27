"""Architecture guarantees for Executive Intelligence."""

from __future__ import annotations

import ast
from pathlib import Path

EXECUTIVE_INTELLIGENCE_DOMAIN = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "domain"
    / "executive_intelligence"
)
EXECUTIVE_INTELLIGENCE_APPLICATION = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "application"
    / "executive_intelligence"
)
EXECUTIVE_INTELLIGENCE_API = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "api"
    / "executive_intelligence"
)

_FORBIDDEN_APPLICATION_PREFIXES = (
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
    "codestrata_platform.rag",
    "codestrata_engine",
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


def test_executive_intelligence_domain_has_no_infrastructure_imports() -> None:
    for path in sorted(EXECUTIVE_INTELLIGENCE_DOMAIN.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module
            assert not module.startswith("codestrata_platform.rag")
            assert not module.startswith("codestrata_engine")


def test_executive_intelligence_application_forbids_disallowed_imports() -> None:
    for path in sorted(EXECUTIVE_INTELLIGENCE_APPLICATION.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in source
        assert "boto3" not in source
        for module in _imported_modules(path):
            assert not any(
                module.startswith(prefix) for prefix in _FORBIDDEN_APPLICATION_PREFIXES
            ), f"{path.name} imports forbidden module {module}"


def test_executive_intelligence_aggregation_consumes_portfolio_snapshot_only() -> None:
    aggregation = EXECUTIVE_INTELLIGENCE_APPLICATION / "aggregation.py"
    modules = _imported_modules(aggregation)
    assert any(
        module.startswith("codestrata_platform.domain.portfolio") for module in modules
    )
    for module in modules:
        assert not any(
            module.startswith(prefix) for prefix in _FORBIDDEN_APPLICATION_PREFIXES
        )
        assert not module.startswith("codestrata_platform.domain.engineering")


def test_executive_intelligence_api_calls_application_only() -> None:
    for path in sorted(EXECUTIVE_INTELLIGENCE_API.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module
            assert not any(
                module.startswith(prefix) for prefix in _FORBIDDEN_APPLICATION_PREFIXES
            )
