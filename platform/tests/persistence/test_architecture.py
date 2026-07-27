"""Architecture guards for the Platform persistence boundary."""

from __future__ import annotations

import ast
from pathlib import Path

PLATFORM_SRC = (
    Path(__file__).resolve().parents[2] / "src" / "codestrata_platform"
)
DOMAIN_ROOT = PLATFORM_SRC / "domain"
APPLICATION_ROOT = PLATFORM_SRC / "application"
PERSISTENCE_ROOT = PLATFORM_SRC / "infrastructure" / "persistence"

FORBIDDEN_IN_DOMAIN_APP = {
    "sqlalchemy",
    "codestrata_platform.infrastructure",
}


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


def _is_forbidden(module_name: str) -> bool:
    root = module_name.split(".", 1)[0]
    if root in FORBIDDEN_IN_DOMAIN_APP:
        return True
    if module_name.startswith("codestrata_platform.infrastructure"):
        return True
    return False


def test_domain_has_no_persistence_dependencies() -> None:
    forbidden: list[str] = []
    for path in sorted(DOMAIN_ROOT.rglob("*.py")):
        for module in _imported_modules(path):
            if _is_forbidden(module) or module.startswith("sqlalchemy"):
                forbidden.append(f"{path.relative_to(DOMAIN_ROOT)}:{module}")
    assert forbidden == []


def test_application_has_no_persistence_dependencies() -> None:
    forbidden: list[str] = []
    for path in sorted(APPLICATION_ROOT.rglob("*.py")):
        for module in _imported_modules(path):
            if _is_forbidden(module) or module.startswith("sqlalchemy"):
                forbidden.append(f"{path.relative_to(APPLICATION_ROOT)}:{module}")
    assert forbidden == []


def test_orm_records_are_not_reexported_from_domain_or_application() -> None:
    for root in (DOMAIN_ROOT, APPLICATION_ROOT):
        for path in sorted(root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            assert "OrganizationRecord" not in source
            assert "WorkspaceRecord" not in source
            assert "RepositoryRecord" not in source
            assert "AssessmentRecord" not in source


def test_persistence_package_exists_with_required_layout() -> None:
    assert (PERSISTENCE_ROOT / "database.py").is_file()
    assert (PERSISTENCE_ROOT / "unit_of_work.py").is_file()
    assert (PERSISTENCE_ROOT / "models").is_dir()
    assert (PERSISTENCE_ROOT / "mappers").is_dir()
    assert (PERSISTENCE_ROOT / "repositories").is_dir()
    assert (PERSISTENCE_ROOT / "migrations").is_dir()
