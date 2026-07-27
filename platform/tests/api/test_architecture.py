"""Architecture guards for the Platform REST transport layer."""

from __future__ import annotations

import ast
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2] / "src" / "codestrata_platform" / "api"
CONTROLLERS_ROOT = API_ROOT / "controllers"

RECORD_MARKERS = (
    "InMemory",
    "SqlAlchemy",
    "OrganizationRecord",
    "WorkspaceRecord",
    "RepositoryRecord",
    "AssessmentRecord",
)


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def test_controllers_do_not_access_repositories_or_orm() -> None:
    violations: list[str] = []
    for path in sorted(CONTROLLERS_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for marker in RECORD_MARKERS:
            if marker in source:
                violations.append(f"{path.name}:{marker}")
        for module in _imports(path):
            if module.startswith("codestrata_platform.infrastructure"):
                violations.append(f"{path.name}:import:{module}")
            if module.startswith("sqlalchemy"):
                violations.append(f"{path.name}:import:{module}")
    assert violations == []


def test_controllers_invoke_application_services_only() -> None:
    for path in sorted(CONTROLLERS_ROOT.rglob("*.py")):
        if path.parent == CONTROLLERS_ROOT and path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        if path.parent.name in {"organizations", "workspaces", "repositories", "assessments"}:
            assert "services." in source
            assert "APIRouter" in source


def test_dto_layer_does_not_import_domain_aggregates() -> None:
    dto_root = API_ROOT / "dto"
    violations: list[str] = []
    for path in sorted(dto_root.rglob("*.py")):
        for module in _imports(path):
            if module.endswith(".aggregate"):
                violations.append(f"{path.name}:{module}")
    assert violations == []
