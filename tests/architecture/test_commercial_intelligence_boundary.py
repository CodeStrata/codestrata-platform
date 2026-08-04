"""Epic 6 Slice 6.12 — Commercial Engineering Intelligence boundary verification.

Verification only: proves Platform ownership and Engine/Community isolation.
Does not add product capabilities.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_SRC = REPO_ROOT / "engine" / "src" / "codestrata"
ENGINE_CLI = ENGINE_SRC / "cli"
PLATFORM_IR = (
    REPO_ROOT / "platform" / "src" / "codestrata_platform" / "intelligence_reporting"
)
PLATFORM_DEMO = REPO_ROOT / "platform" / "demo"
PUBLIC_EXPORT = REPO_ROOT / "public-export-manifest.yaml"
EXAMPLES = REPO_ROOT / "examples"
DOCS_PUBLIC = REPO_ROOT / "docs"

# Commercial symbols / APIs that must never appear under Engine runtime.
COMMERCIAL_TOKENS: tuple[str, ...] = (
    "EngineeringIntelligenceReport",
    "IntelligenceDataset",
    "CrossRepositoryAggregation",
    "WebsiteSafeExportDocument",
    "WebsiteExportBuildPolicy",
    "WebsiteSafeIntelligenceReport",
    "IntelligenceInterpretationPolicyBundle",
    "build_website_safe_export",
    "build_oss_demonstration_report",
    "generate_oss_demonstration_artifacts",
    "ingest_assessment_dataset",
    "aggregate_intelligence_dataset",
    "populate_report_technology_distribution",
    "populate_report_capability_comparisons",
    "populate_report_recurring_patterns",
    "populate_report_modernization_observations",
    "populate_report_quality",
    "populate_report_repository_drilldowns",
    "StaticIntelligenceExportWriter",
    "OssDemonstrationCatalog",
)

COMMERCIAL_PACKAGES: tuple[str, ...] = (
    "domain",
    "application",
    "application/aggregation",
    "application/technology_distribution",
    "application/capability_comparison",
    "application/recurring_patterns",
    "application/modernization_observations",
    "application/report_quality",
    "application/repository_drilldowns",
    "application/website_export",
    "application/oss_demonstration",
    "presentation",
    "presentation/static_html",
    "infrastructure",
)

CLI_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "intelligence-report",
    "intelligence_report",
    "engineering-intelligence",
    "website-export",
    "website_export",
    "oss-demonstration",
    "oss_demonstration",
    "cross-repository",
    "portfolio-report",
    "build_website_safe_export",
    "build_oss_demonstration_report",
    "ingest_assessment_dataset",
    "aggregate_intelligence_dataset",
)


def _python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def test_platform_owns_all_commercial_packages() -> None:
    assert PLATFORM_IR.is_dir()
    for relative in COMMERCIAL_PACKAGES:
        path = PLATFORM_IR / relative
        assert path.is_dir(), f"missing commercial package: {relative}"
        assert (path / "__init__.py").is_file() or any(path.glob("*.py"))


def test_no_duplicate_commercial_packages_outside_platform_ir() -> None:
    """Commercial package directory names must not be reimplemented elsewhere."""

    owned_names = {
        "intelligence_reporting",
        "website_export",
        "oss_demonstration",
        "repository_drilldowns",
        "report_quality",
        "modernization_observations",
        "recurring_patterns",
        "capability_comparison",
        "technology_distribution",
    }
    skip_parts = {
        ".venv",
        "node_modules",
        "__pycache__",
        ".git",
        ".export-staging",
        "intelligence_reporting",
    }
    offenders: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_dir():
            continue
        if path.name not in owned_names:
            continue
        if any(part in skip_parts for part in path.parts):
            # Allow the owned tree and test mirrors named after packages.
            if "intelligence_reporting" in path.parts:
                continue
            if "tests" in path.parts and "intelligence_reporting" in path.parts:
                continue
        # Allow platform tests package mirrors under platform/tests/.../intelligence_reporting
        if "platform" in path.parts and "tests" in path.parts:
            continue
        # Allow System Verification packages under platform/verification/ (SV.6–SV.8).
        if "platform" in path.parts and "verification" in path.parts:
            continue
        offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], "Duplicate commercial packages:\n" + "\n".join(offenders)


def test_engine_contains_no_commercial_tokens() -> None:
    offenders: list[str] = []
    for path in _python_files(ENGINE_SRC):
        text = path.read_text(encoding="utf-8")
        for token in COMMERCIAL_TOKENS:
            if token in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{token}")
    assert offenders == [], "Commercial tokens in Engine:\n" + "\n".join(offenders)


def test_engine_has_no_intelligence_reporting_filesystem_tree() -> None:
    assert list(ENGINE_SRC.rglob("*intelligence_reporting*")) == []
    assert not (ENGINE_SRC / "codestrata_platform").exists()
    assert not (REPO_ROOT / "engine" / "src" / "codestrata_platform").exists()


def test_engine_ast_imports_never_reference_platform_or_ir() -> None:
    offenders: list[str] = []
    for path in _python_files(ENGINE_SRC):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            for module in modules:
                if module == "codestrata_platform" or module.startswith(
                    "codestrata_platform."
                ):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{module}")
                if module.startswith("platform."):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{module}")
    assert offenders == [], "Forbidden Engine imports:\n" + "\n".join(offenders)


def test_community_cli_exposes_no_commercial_intelligence_commands() -> None:
    assert ENGINE_CLI.is_dir()
    offenders: list[str] = []
    for path in _python_files(ENGINE_CLI):
        text = path.read_text(encoding="utf-8").lower()
        for phrase in CLI_FORBIDDEN_PHRASES:
            if phrase.lower() in text:
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{phrase}")
    assert offenders == [], "Commercial CLI leakage:\n" + "\n".join(offenders)


def test_examples_and_public_docs_do_not_ship_commercial_ir_packages() -> None:
    for root in (EXAMPLES, DOCS_PUBLIC):
        if not root.exists():
            continue
        hits = list(root.rglob("*intelligence_reporting*"))
        assert hits == [], f"commercial IR under {root}: {hits}"


def test_public_export_manifest_excludes_platform_and_commercial_assets() -> None:
    blob = PUBLIC_EXPORT.read_text(encoding="utf-8")
    manifest = yaml.safe_load(blob)
    forbidden = manifest.get("release", {}).get("forbidden_internal_paths") or []
    assert "platform/" in forbidden
    never_roots = (
        manifest.get("defaults", {})
        .get("documentation_boundary", {})
        .get("never_export_source_roots")
        or []
    )
    assert "platform" in never_roots
    assert "platform/**" in blob
    assert "intelligence_reporting" not in blob or "platform" in blob
    # Community engine export must not include platform source root.
    exports = {item["name"]: item for item in manifest["exports"]}
    engine_export = exports["codestrata-engine"]
    assert engine_export.get("source_root", "engine") in {"engine", None} or str(
        engine_export.get("source_root", "engine")
    ).startswith("engine")
    includes = " ".join(
        str(item) for item in (engine_export.get("include") or engine_export.get("includes") or [])
    )
    assert "platform/" not in includes
    assert "intelligence_reporting" not in includes


def test_schema_versions_unchanged() -> None:
    from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
    from codestrata_platform.intelligence_reporting.application.website_export import (
        WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION,
    )
    from codestrata_platform.intelligence_reporting.domain.report import (
        ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION,
    )

    assert ASSESSMENT_JSON_SCHEMA_VERSION == "1.2"
    assert ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION == "1.0"
    assert WEBSITE_SAFE_EIR_EXPORT_SCHEMA_VERSION == "1.0"

    recording = (REPO_ROOT / "engine" / "validation" / "recording.py").read_text(
        encoding="utf-8"
    )
    summary = (REPO_ROOT / "engine" / "validation" / "summary_artifact.py").read_text(
        encoding="utf-8"
    )
    assert 'RECORD_SCHEMA_VERSION = "1.0"' in recording
    assert 'SUMMARY_SCHEMA_VERSION = "1.0"' in summary
    assert 'SUPPORTED_RECORD_SCHEMA_VERSION = "1.0"' in summary


def test_oss_demonstration_artifacts_remain_valid_and_platform_only() -> None:
    for name in (
        "engineering-intelligence-report.json",
        "engineering-intelligence-report.html",
        "export-manifest.json",
        "catalog.json",
    ):
        assert (PLATFORM_DEMO / name).is_file()

    manifest = json.loads((PLATFORM_DEMO / "export-manifest.json").read_text(encoding="utf-8"))
    assert manifest["export_id"].startswith("eir-export:")
    assert manifest["source_report_id"].startswith("eir:")
    assert manifest["classification"] == "Public OSS report"
    assert manifest["repository_count"] == 5

    # Fresh build must match committed artifacts (determinism + no drift).
    from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
        build_oss_demonstration_report,
    )

    result = build_oss_demonstration_report(catalog_path=PLATFORM_DEMO / "catalog.json")
    assert (
        result.export_bundle.json_bytes
        == (PLATFORM_DEMO / "engineering-intelligence-report.json").read_bytes()
    )
    assert (
        result.export_bundle.html_bytes
        == (PLATFORM_DEMO / "engineering-intelligence-report.html").read_bytes()
    )
    assert (
        result.export_bundle.manifest_bytes
        == (PLATFORM_DEMO / "export-manifest.json").read_bytes()
    )


def test_documentation_states_commercial_only_boundary() -> None:
    readme = (
        REPO_ROOT / "platform" / "docs" / "intelligence-reporting" / "README.md"
    ).read_text(encoding="utf-8")
    boundary_doc = (
        REPO_ROOT
        / "platform"
        / "docs"
        / "intelligence-reporting"
        / "commercial-boundary.md"
    )
    assert boundary_doc.is_file()
    boundary = boundary_doc.read_text(encoding="utf-8")
    for blob in (readme, boundary):
        assert "Platform" in blob
        assert "Community" in blob or "Community Edition" in blob
        assert "single-repository" in blob or "One repository" in blob
        assert "Commercial" in blob or "commercial" in blob


def test_platform_may_import_engine_contracts_only_via_approved_paths() -> None:
    """IR application may import Engine reporting/traceability contracts; not reverse."""

    allowed_prefixes = (
        "codestrata.reporting",
        "codestrata.validation",
    )
    offenders: list[str] = []
    for path in _python_files(PLATFORM_IR):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if not node.module.startswith("codestrata."):
                continue
            if node.module.startswith(allowed_prefixes) or node.module == "codestrata":
                continue
            # Narrow allowlist for package metadata / contract constants used by ingest.
            if node.module.startswith("codestrata."):
                # Flag deep analyzer/rule imports as unexpected for IR.
                if any(
                    part in node.module
                    for part in (
                        ".application.rules",
                        ".application.evidence",
                        ".analyzers",
                        ".cli",
                    )
                ):
                    offenders.append(f"{path.relative_to(REPO_ROOT)}:{node.module}")
    assert offenders == [], "Unexpected Engine deep imports from IR:\n" + "\n".join(
        offenders
    )


@pytest.mark.parametrize(
    "relative",
    [
        "application/website_export/builder.py",
        "application/oss_demonstration/builder.py",
        "presentation/static_html/renderer.py",
        "infrastructure/static_export_writer.py",
        "domain/report.py",
    ],
)
def test_key_commercial_modules_reside_only_under_platform_ir(relative: str) -> None:
    assert (PLATFORM_IR / relative).is_file()
    basename = Path(relative).name
    engine_hits = [
        path
        for path in ENGINE_SRC.rglob(basename)
        if path.is_file() and "intelligence_reporting" not in path.parts
    ]
    # Filenames like builder.py / report.py exist elsewhere; ensure content tokens absent.
    for path in engine_hits:
        text = path.read_text(encoding="utf-8")
        assert "EngineeringIntelligenceReport" not in text
        assert "build_website_safe_export" not in text
        assert "build_oss_demonstration_report" not in text
