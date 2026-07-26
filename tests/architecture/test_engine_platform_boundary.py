"""Architectural boundary: Community Engine must not depend on platform/."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_SRC = REPO_ROOT / "engine" / "src"
PLATFORM = REPO_ROOT / "platform"

FORBIDDEN_IMPORT_RE = re.compile(
    r"^\s*(?:from|import)\s+(codestrata_platform\b|platform\.[A-Za-z_])",
    re.MULTILINE,
)
FORBIDDEN_PATH_RE = re.compile(
    r"""['"](?:\.\./)*platform/""",
)
UNIVERSITY_RE = re.compile(
    r"platform[/\\]enterprise[/\\]examples[/\\]university|"
    r"(?<!/)enterprise[/\\]examples[/\\]university"
)


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def test_platform_directory_exists() -> None:
    assert PLATFORM.is_dir()
    assert (PLATFORM / "src" / "codestrata_platform").is_dir()
    assert not (PLATFORM / "enterprise").exists()


def test_root_has_no_legacy_aimf_package() -> None:
    assert not (REPO_ROOT / "src" / "aimf").exists()
    assert not (REPO_ROOT / "src").exists()


def test_no_university_references_in_source_tests_docs_manifest() -> None:
    roots = [
        REPO_ROOT / "engine",
        REPO_ROOT / "platform",
        REPO_ROOT / "tests",
        REPO_ROOT / "scripts",
        REPO_ROOT / "examples",
        REPO_ROOT / "docs",
    ]
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {
                ".py",
                ".md",
                ".toml",
                ".yaml",
                ".yml",
                ".txt",
                ".json",
            }:
                continue
            if "__pycache__" in path.parts or ".export-staging" in path.parts:
                continue
            files.append(path)
    for extra in (
        REPO_ROOT / "README.md",
        REPO_ROOT / "ARCHITECTURE.md",
        REPO_ROOT / "ROADMAP.md",
        REPO_ROOT / "CHANGELOG.md",
        REPO_ROOT / "public-export-manifest.yaml",
        REPO_ROOT / "platform" / "README.md",
    ):
        if extra.is_file():
            files.append(extra)

    offenders: list[str] = []
    skip = {
        Path("tests/architecture/test_engine_platform_boundary.py"),
    }
    for path in sorted(set(files)):
        rel = path.relative_to(REPO_ROOT)
        if rel in skip:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if UNIVERSITY_RE.search(text):
            offenders.append(str(rel))
    assert not offenders, "Stale university workspace references:\n" + "\n".join(
        offenders
    )


def test_engine_has_no_platform_imports() -> None:
    offenders: list[str] = []
    for path in _python_files(ENGINE_SRC):
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_IMPORT_RE.search(text):
            offenders.append(str(path.relative_to(REPO_ROOT)))
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("platform."):
                        offenders.append(str(path.relative_to(REPO_ROOT)))
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("platform."):
                    offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, "Engine imports platform modules:\n" + "\n".join(offenders)


def test_engine_has_no_platform_path_literals() -> None:
    """Hard-coded platform/ paths in engine runtime code are forbidden."""

    offenders: list[str] = []
    runtime_roots = [
        ENGINE_SRC / "codestrata",
    ]
    for root in runtime_roots:
        for path in _python_files(root):
            text = path.read_text(encoding="utf-8")
            code_lines = [
                line
                for line in text.splitlines()
                if not line.strip().startswith("#")
            ]
            joined = "\n".join(code_lines)
            if FORBIDDEN_PATH_RE.search(joined):
                offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, "Engine runtime references platform/ paths:\n" + "\n".join(
        offenders
    )


def test_engine_package_metadata_is_self_contained() -> None:
    pyproject = (REPO_ROOT / "engine" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "codestrata"' in pyproject
    assert "platform/" not in pyproject
    assert "pgvector" not in pyproject
    assert (REPO_ROOT / "engine" / "LICENSE").is_file()
    assert (REPO_ROOT / "engine" / "src" / "codestrata" / "__init__.py").is_file()


def test_platform_package_depends_on_engine() -> None:
    pyproject = (REPO_ROOT / "platform" / "pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "codestrata-platform"' in pyproject
    assert "codestrata>=" in pyproject
    assert (PLATFORM / "src" / "codestrata_platform" / "rag").is_dir()
    assert (PLATFORM / "src" / "codestrata_platform" / "knowledge_graph").is_dir()


def test_public_export_manifest_lists_four_mirrors() -> None:
    import yaml

    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    names = {item["name"] for item in manifest["exports"]}
    assert names == {
        "codestrata-engine",
        "codestrata-examples",
        "codestrata-cursor",
        "codestrata-vscode",
    }
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "university" not in blob.lower() or "forbid" in blob.lower()


@pytest.mark.parametrize(
    "plugin",
    ["cursor-plugin", "vscode-plugin"],
)
def test_plugin_placeholders_only(plugin: str) -> None:
    root = REPO_ROOT / plugin
    assert (root / "README.md").is_file()
    assert (root / "PLACEHOLDER.md").is_file()
    files = sorted(
        path.name
        for path in root.iterdir()
        if path.is_file() and path.name != ".DS_Store"
    )
    assert set(files) <= {"README.md", "PLACEHOLDER.md", ".gitkeep"}
