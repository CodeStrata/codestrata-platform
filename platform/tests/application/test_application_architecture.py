"""Architectural guarantees for the Commercial Platform application layer."""

from __future__ import annotations

import ast
from pathlib import Path

APPLICATION_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "application"
)

ALLOWED_ROOTS = {
    "__future__",
    "annotations",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "enum",
    "hashlib",
    "json",
    "os",
    "re",
    "typing",
    "codestrata_platform",
}

FORBIDDEN_MARKERS = (
    "sqlalchemy",
    "psycopg",
    "alembic",
    "fastapi",
    "starlette",
    "pgvector",
)


def _module_allowed(module_name: str) -> bool:
    root = module_name.split(".", 1)[0]
    if root not in ALLOWED_ROOTS and module_name not in ALLOWED_ROOTS:
        return False
    if module_name.startswith("codestrata_platform.infrastructure"):
        return False
    if module_name.startswith("codestrata_platform.rag"):
        return False
    if module_name.startswith("codestrata_platform.knowledge_graph"):
        return False
    return True


def test_application_does_not_import_infrastructure() -> None:
    forbidden: list[str] = []
    for path in sorted(APPLICATION_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not _module_allowed(alias.name):
                        forbidden.append(f"{path.relative_to(APPLICATION_ROOT)}:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                if not _module_allowed(node.module):
                    forbidden.append(f"{path.relative_to(APPLICATION_ROOT)}:{node.module}")
    assert forbidden == []


def test_application_avoids_persistence_frameworks() -> None:
    offenders: list[str] = []
    for path in sorted(APPLICATION_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_MARKERS:
            if marker in source:
                offenders.append(f"{path.relative_to(APPLICATION_ROOT)}:{marker}")
    assert offenders == []


def test_application_services_use_constructor_injection() -> None:
    service_files = [
        APPLICATION_ROOT / "repository" / "service.py",
        APPLICATION_ROOT / "assessment" / "service.py",
        APPLICATION_ROOT / "workspace" / "service.py",
        APPLICATION_ROOT / "organization" / "service.py",
        APPLICATION_ROOT / "artifact" / "service.py",
        APPLICATION_ROOT / "intelligence" / "service.py",
        APPLICATION_ROOT / "engineering" / "service.py",
        APPLICATION_ROOT / "knowledge_graph" / "services.py",
        APPLICATION_ROOT / "knowledge_graph" / "intelligence" / "services.py",
    ]
    for path in service_files:
        source = path.read_text(encoding="utf-8")
        assert "def __init__(" in source
        assert "@" not in source or all(
            marker not in source
            for marker in ("@Injectable", "@Service", "@Component", "@Autowired")
        )
