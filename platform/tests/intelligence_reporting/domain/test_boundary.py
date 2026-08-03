"""Commercial boundary tests for intelligence_reporting."""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path

import yaml


PLATFORM_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PLATFORM_ROOT.parent
ENGINE_SRC = REPO_ROOT / "engine" / "src"
PLATFORM_PKG = PLATFORM_ROOT / "src" / "codestrata_platform" / "intelligence_reporting"


def test_platform_package_exists() -> None:
    assert PLATFORM_PKG.is_dir()
    assert (PLATFORM_PKG / "domain" / "report.py").is_file()
    mod = importlib.import_module("codestrata_platform.intelligence_reporting")
    assert mod.ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"


def test_engine_tree_has_no_intelligence_reporting_package() -> None:
    engine_hits = list((ENGINE_SRC / "codestrata").rglob("*intelligence_reporting*"))
    assert engine_hits == []


def test_no_commercial_classes_under_engine() -> None:
    forbidden = (
        "EngineeringIntelligenceReport",
        "IntelligenceDataset",
        "WebsiteSafeIntelligenceReport",
    )
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in forbidden:
            assert name not in text, f"{name} found in {path}"


def test_community_cli_has_no_intelligence_report_command() -> None:
    cli_root = REPO_ROOT / "engine" / "src" / "codestrata" / "cli"
    hits: list[str] = []
    if cli_root.exists():
        for path in cli_root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "intelligence-report" in text or "intelligence_report" in text:
                hits.append(str(path.relative_to(REPO_ROOT)))
    assert hits == []


def test_public_export_excludes_platform_package() -> None:
    blob = (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    assert "platform/**" in blob
    assert "platform/" in blob
    manifest = yaml.safe_load(blob)
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden
    for export in manifest["exports"]:
        assert export.get("source_root") != "platform"


def test_intelligence_reporting_module_originates_from_platform_tree() -> None:
    mod = importlib.import_module("codestrata_platform.intelligence_reporting")
    module_path = Path(mod.__file__).resolve()
    assert "platform" in module_path.parts
    assert "engine" not in module_path.parts


def test_engine_source_does_not_import_platform_intelligence() -> None:
    for path in (ENGINE_SRC / "codestrata").rglob("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(
                        "codestrata_platform.intelligence_reporting"
                    )
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(
                    "codestrata_platform.intelligence_reporting"
                )


def test_engine_isolated_import_does_not_load_platform_from_engine_src() -> None:
    """Engine source tree does not contain the commercial package path."""

    assert not (ENGINE_SRC / "codestrata_platform").exists()
    code = (
        "import importlib.util, sys\n"
        f"sys.path = [{str(ENGINE_SRC)!r}]\n"
        "spec = importlib.util.find_spec('codestrata_platform')\n"
        "raise SystemExit(0 if spec is None else 'found')\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "found" not in (result.stdout + result.stderr)
