"""Architecture guarantees for Portfolio Intelligence."""

from __future__ import annotations

import ast
from pathlib import Path

PORTFOLIO_DOMAIN = (
    Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "domain" / "portfolio"
)
PORTFOLIO_APPLICATION = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "application"
    / "portfolio"
)
PORTFOLIO_API = (
    Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "api" / "portfolio"
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


def test_portfolio_domain_has_no_infrastructure_imports() -> None:
    for path in sorted(PORTFOLIO_DOMAIN.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module
            assert not module.startswith("codestrata_platform.rag")


def test_portfolio_application_has_no_sqlalchemy_or_llm() -> None:
    for path in sorted(PORTFOLIO_APPLICATION.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in source
        modules = _imported_modules(path)
        assert not any(
            module.startswith("codestrata_platform.infrastructure") for module in modules
        )
        assert not any(module.startswith("codestrata_platform.rag") for module in modules)
        assert "openai" not in source.lower()


def test_portfolio_api_calls_application_only() -> None:
    for path in sorted(PORTFOLIO_API.rglob("*.py")):
        modules = _imported_modules(path)
        assert not any(
            module.startswith("codestrata_platform.infrastructure") for module in modules
        )
        assert not any(
            module.startswith("codestrata_platform.domain.engineering") for module in modules
        )
        assert any(
            module.startswith("codestrata_platform.application.portfolio") for module in modules
        ) or path.name in {"__init__.py", "dto.py"}


def test_aggregation_consumes_portfolio_source_ports_only() -> None:
    path = PORTFOLIO_APPLICATION / "aggregation.py"
    modules = _imported_modules(path)
    forbidden = (
        "codestrata_platform.rag",
        "codestrata_platform.application.answering",
        "codestrata_platform.application.retrieval",
        "codestrata_platform.infrastructure",
    )
    assert not any(module.startswith(prefix) for module in modules for prefix in forbidden)
    source = path.read_text(encoding="utf-8")
    assert "llm" not in source.lower()
    assert "openai" not in source.lower()
