"""Architectural guarantees for the Commercial Platform domain foundation."""

from __future__ import annotations

import ast
from pathlib import Path

DOMAIN_ROOT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "domain"
)

ALLOWED_STDLIB = {
    "__future__",
    "annotations",
    "collections",
    "collections.abc",
    "dataclasses",
    "datetime",
    "enum",
    "hashlib",
    "re",
    "typing",
    "uuid",
}


def _is_allowed(module_name: str) -> bool:
    if module_name in ALLOWED_STDLIB:
        return True
    if module_name.startswith("codestrata_platform.domain"):
        return True
    return False


def test_domain_has_no_framework_dependencies() -> None:
    forbidden: list[str] = []
    for path in sorted(DOMAIN_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not _is_allowed(alias.name) and not _is_allowed(
                        alias.name.split(".", 1)[0]
                    ):
                        # Only allow exact stdlib roots via ALLOWED_STDLIB membership.
                        root = alias.name.split(".", 1)[0]
                        if root not in ALLOWED_STDLIB:
                            forbidden.append(f"{path.name}:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                if _is_allowed(node.module):
                    continue
                root = node.module.split(".", 1)[0]
                if root not in ALLOWED_STDLIB:
                    forbidden.append(f"{path.name}:{node.module}")
    assert forbidden == []


def test_application_contracts_are_protocols_only() -> None:
    contracts_root = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "codestrata_platform"
        / "application"
        / "contracts"
    )
    assert contracts_root.is_dir()
    for path in sorted(contracts_root.glob("*.py")):
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8")
        assert "class " in source
        assert "Protocol" in source
        # No concrete service bodies beyond protocol method signatures.
        assert "def __init__" not in source
