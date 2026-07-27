"""Architecture guarantees for Engineering Answering."""

from __future__ import annotations

import ast
from pathlib import Path

ANSWERING_DOMAIN = (
    Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "domain" / "answering"
)
ANSWERING_APPLICATION = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "application"
    / "answering"
)
ANSWERING_API = (
    Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "api" / "answering"
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


def test_answering_domain_has_no_infrastructure_imports() -> None:
    for path in sorted(ANSWERING_DOMAIN.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module
            assert not module.startswith("codestrata_platform.rag")


def test_answering_application_has_no_provider_sdk_or_sqlalchemy() -> None:
    for path in sorted(ANSWERING_APPLICATION.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "sqlalchemy" not in source
        assert "openai" not in source.lower() or "model_id" in source
        assert "boto3" not in source
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert not module.startswith("codestrata_platform.rag")
            assert not module.startswith("codestrata_engine")


def test_answering_api_calls_application_only() -> None:
    for path in sorted(ANSWERING_API.rglob("*.py")):
        for module in _imported_modules(path):
            assert not module.startswith("codestrata_platform.infrastructure")
            assert "sqlalchemy" not in module


def test_answer_service_consumes_retrieval_context_only() -> None:
    services = ANSWERING_APPLICATION / "services.py"
    modules = _imported_modules(services)
    assert any(
        module.startswith("codestrata_platform.application.retrieval") for module in modules
    )
    forbidden = (
        "codestrata_platform.domain.artifact",
        "codestrata_platform.domain.intelligence",
        "codestrata_engine",
        "codestrata_platform.rag",
    )
    for module in modules:
        assert not any(module.startswith(prefix) for prefix in forbidden)
