"""Path classification rules for Slice 16.1 (audit-only; no mutations)."""

from __future__ import annotations

from pathlib import PurePosixPath

from verification.repository_inventory.contract import CLASSIFICATIONS

# Authoritative token source; other copies are DUPLICATE / EXPORT_ONLY / GENERATED.
AUTHORITATIVE_TOKENS = "design-system/tokens/tokens.css"

ACTIVE_DOC_ROOTS = (
    "docs/getting-started",
    "docs/extensions",
    "docs/ai-providers",
    "docs/community",
    "docs/engine",
    "docs/faq",
    "docs/troubleshooting",
    "docs/public",
    "docs/reference",
    "docs/security",
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "ARCHITECTURE.md",
)

STALE_DOC_HINTS = (
    "docs/platform/",
    "docs/internal/",
    "platform/docs/",
    "ROADMAP.md",
)

LEGACY_HINTS = (
    "aimf",
    "cursor-plugin",
    "codestrata-cursor",
)

HISTORICAL_PREFIXES = (
    ".export-staging/codestrata-cursor/",
    "reports/verification/sv12-",
    "reports/verification/sv13-",
    "reports/verification/sv14-",
    "reports/verification/sv15-",
    "validation/repos/",
)

GENERATED_PREFIXES = (
    "dist/",
    ".generated/",
    "insights/dist/",
    "platform/dist/",
    "docs/.vitepress/dist/",
    "vscode-plugin/out/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".codestrata/",
    "engine/.codestrata/",
    "reports/validation/",
)

EXPORT_PREFIXES = (
    ".export-staging/",
)

DELETE_CANDIDATE_HINTS = (
    ".DS_Store",
    ".tmp",
    ".temp",
    "~",
    ".bak",
    ".orig",
    ".swp",
)


def area_for_path(rel: str) -> str:
    p = PurePosixPath(rel)
    parts = p.parts
    if not parts:
        return "root"
    top = parts[0]
    mapping = {
        "engine": "engine",
        "platform": "platform",
        "infrastructure": "infrastructure",
        "vscode-plugin": "vscode-plugin",
        "insights": "insights",
        "docs": "docs",
        "design-system": "design-system",
        "verification": "verification",
        "tests": "tests",
        "reports": "reports",
        "scripts": "scripts",
        "governance": "governance",
        "knowledge": "knowledge",
        "examples": "examples",
        "validation": "validation",
        "test-fixtures": "tests",
        ".export-staging": "export_targets",
        ".generated": "generated",
        "dist": "build_outputs",
        ".codestrata": "generated",
        ".codestrata-examples": "demo",
        ".codestrata-test-knowledge": "generated",
        ".cursor": "historical",
    }
    if top in mapping:
        return mapping[top]
    if rel.endswith(".json") and "polic" in rel.lower():
        return "policies"
    if "contract" in rel.lower():
        return "contracts"
    if top.startswith("."):
        return "generated"
    return "root"


def kind_for_path(rel: str, is_dir: bool) -> str:
    if is_dir:
        return "directory"
    name = PurePosixPath(rel).name.lower()
    if name.endswith((".sqlite", ".db")):
        return "sqlite"
    if name.endswith((".png", ".svg", ".ico", ".jpg", ".jpeg", ".webp")):
        return "asset"
    if name.endswith((".css",)):
        return "css"
    if name.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")):
        return "typescript_js"
    if name.endswith((".py",)):
        return "python"
    if name.endswith((".md", ".mdx")):
        return "markdown"
    if name.endswith((".json", ".yaml", ".yml", ".toml")):
        return "config"
    if name.endswith((".tf", ".tfvars", ".hcl")):
        return "infrastructure"
    if name in ("dockerfile",) or name.startswith("dockerfile"):
        return "container"
    return "file"


def classify_path(rel: str, *, is_dir: bool = False, empty: bool = False) -> tuple[str, str, list[str]]:
    """Return (primary_classification, notes, secondary)."""
    secondary: list[str] = []
    lower = rel.lower().replace("\\", "/")
    notes = ""

    if empty and is_dir:
        return "EMPTY", "empty_directory", secondary

    for hint in DELETE_CANDIDATE_HINTS:
        if hint in PurePosixPath(rel).name or lower.endswith(hint):
            return "DELETE_CANDIDATE", f"temp_or_junk:{hint}", secondary

    if lower.endswith("node_modules") or "/node_modules/" in lower:
        return "DELETE_CANDIDATE", "node_modules_should_not_be_committed", ["GENERATED"]

    for prefix in EXPORT_PREFIXES:
        if lower.startswith(prefix) or rel.startswith(prefix.rstrip("/")):
            if "codestrata-cursor" in lower:
                return "HISTORICAL", "export_staging_cursor_historical", ["EXPORT_ONLY", "LEGACY"]
            return "EXPORT_ONLY", "export_staging", secondary

    for prefix in GENERATED_PREFIXES:
        if rel.startswith(prefix) or lower.startswith(prefix):
            cls = "GENERATED"
            if "/dist/" in f"/{lower}" or rel.endswith("/dist") or rel == "dist":
                secondary.append("DELETE_CANDIDATE")
                notes = "build_output"
            elif lower.endswith((".sqlite", ".db")):
                notes = "local_sqlite_generated"
            else:
                notes = "generated_artifact"
            return cls, notes, secondary

    for prefix in HISTORICAL_PREFIXES:
        if rel.startswith(prefix) or lower.startswith(prefix):
            return "HISTORICAL", "historical_verification_or_fixture", secondary

    if rel == AUTHORITATIVE_TOKENS:
        return "ACTIVE_ASSET", "authoritative_design_tokens", secondary

    if PurePosixPath(rel).name == "tokens.css" and rel != AUTHORITATIVE_TOKENS:
        if "dist/" in lower or ".vitepress/dist" in lower:
            return "GENERATED", "generated_token_copy", ["DUPLICATE"]
        if "export-staging" in lower:
            return "EXPORT_ONLY", "exported_token_copy", ["DUPLICATE"]
        return "DUPLICATE", "non_authoritative_tokens_css_copy", ["ACTIVE_ASSET"]

    if any(h in lower for h in LEGACY_HINTS) and not rel.startswith("verification/"):
        if "cursor" in lower and ("export" in lower or "media" in lower):
            return "HISTORICAL", "legacy_cursor_surface", ["LEGACY"]
        if "aimf" in lower:
            return "LEGACY", "legacy_aimf_reference", ["OWNER_REVIEW_REQUIRED"]

    if rel == "ROADMAP.md":
        return "ARCHIVE_CANDIDATE", "readme_marks_roadmap_archive_candidate", ["STALE"]

    if any(rel.startswith(h) or lower.startswith(h.lower()) for h in STALE_DOC_HINTS):
        if rel.startswith("docs/platform/") or rel.startswith("platform/docs/"):
            return "STALE", "platform_docs_superseded_by_community_docs", [
                "ARCHIVE_CANDIDATE",
                "OWNER_REVIEW_REQUIRED",
            ]
        if rel.startswith("docs/internal/"):
            return "OWNER_REVIEW_REQUIRED", "internal_docs", ["STALE"]

    if rel.startswith("design-system/"):
        if "/policies/" in rel or rel.endswith("policy.json"):
            return "ACTIVE_POLICY", "design_system_policy", secondary
        if "/contracts/" in rel:
            return "ACTIVE_CONTRACT", "design_system_contract", secondary
        if "/assets/" in rel or "/tokens/" in rel:
            return "ACTIVE_ASSET", "design_system_asset", secondary
        if "/documentation/" in rel:
            return "ACTIVE_DOCUMENTATION", "design_system_docs", secondary
        return "ACTIVE_ASSET", "design_system", secondary

    if rel.startswith("verification/"):
        return "ACTIVE_VERIFICATION", "verification_package", secondary

    if rel.startswith("tests/") or rel.startswith("test-fixtures/"):
        return "ACTIVE_TEST", "test_surface", secondary

    if "/policies/" in rel or rel.endswith("_policy.json"):
        return "ACTIVE_POLICY", "policy_artifact", secondary

    if "/contracts/" in rel or rel.endswith(".contract.json"):
        return "ACTIVE_CONTRACT", "contract_artifact", secondary

    if any(rel == d or rel.startswith(d + "/") for d in ACTIVE_DOC_ROOTS if d.endswith(".md")):
        return "ACTIVE_DOCUMENTATION", "root_documentation", secondary
    if any(rel.startswith(d + "/") or rel == d for d in ACTIVE_DOC_ROOTS if not d.endswith(".md")):
        return "ACTIVE_DOCUMENTATION", "community_documentation", secondary
    if rel.startswith("docs/"):
        if "assessments" in lower or "visual-baselines" in lower:
            return "ACTIVE_ASSET", "docs_visual_baseline", secondary
        if rel.startswith("docs/policies/"):
            return "ACTIVE_POLICY", "docs_policy", secondary
        return "ACTIVE_DOCUMENTATION", "docs_tree", secondary

    if rel.startswith("engine/src/") or rel.startswith("platform/src/"):
        return "ACTIVE_RUNTIME", "source_runtime", secondary
    if rel.startswith("vscode-plugin/src/") or rel.startswith("insights/src/"):
        return "ACTIVE_RUNTIME", "client_runtime", secondary
    if rel.startswith("infrastructure/") and not "/.terraform/" in rel:
        return "ACTIVE_RUNTIME", "infrastructure_as_code", secondary
    if rel.startswith("scripts/"):
        return "ACTIVE_RUNTIME", "repo_script", ["OWNER_REVIEW_REQUIRED"]
    if rel.startswith("governance/"):
        if "/assets/" in rel:
            return "ACTIVE_ASSET", "governance_asset", ["DUPLICATE"]
        return "ACTIVE_POLICY", "governance", secondary
    if rel.startswith("knowledge/") or rel.startswith("examples/"):
        return "ACTIVE_ASSET", "knowledge_or_examples", secondary
    if rel.startswith("platform/demo/") or rel.startswith("insights/"):
        if rel.startswith("platform/demo/"):
            return "ACTIVE_ASSET", "demo_content", secondary
        if "/policies/" in rel:
            return "ACTIVE_POLICY", "insights_policy_mirror", ["DUPLICATE"]
        return "ACTIVE_RUNTIME", "insights_surface", secondary
    if rel.startswith("validation/") and not rel.startswith("validation/repos/"):
        return "ACTIVE_VERIFICATION", "validation_harness", secondary

    if lower.endswith((".sqlite", ".db")):
        return "GENERATED", "sqlite_database", ["OWNER_REVIEW_REQUIRED"]

    # Nested package tests / build / docs
    if "/tests/" in f"/{lower}" or rel.endswith("/tests") or "/test/" in f"/{lower}":
        return "ACTIVE_TEST", "nested_tests", secondary
    if "/docs/" in f"/{lower}" and not rel.startswith("docs/"):
        return "ACTIVE_DOCUMENTATION", "nested_package_docs", secondary

    if rel.startswith("engine/"):
        if "/reporting/assets/" in lower or lower.endswith((".png", ".svg")):
            return "ACTIVE_ASSET", "engine_asset", secondary
        return "ACTIVE_RUNTIME", "engine_tree", secondary
    if rel.startswith("platform/"):
        if rel.startswith("platform/demo/"):
            return "ACTIVE_ASSET", "demo_content", secondary
        if "/openapi/" in lower or "/swagger/" in lower:
            return "ACTIVE_CONTRACT", "openapi_surface", ["ACTIVE_ASSET"]
        return "ACTIVE_RUNTIME", "platform_tree", secondary
    if rel.startswith("vscode-plugin/"):
        if "/media/" in lower:
            return "ACTIVE_ASSET", "vscode_media", secondary
        if rel.startswith("vscode-plugin/out/") or "/out/" in lower:
            return "GENERATED", "vscode_compile_out", ["DELETE_CANDIDATE"]
        return "ACTIVE_RUNTIME", "vscode_tree", secondary
    if rel.startswith("insights/"):
        if "/public/" in lower:
            return "ACTIVE_ASSET", "insights_public_assets", secondary
        return "ACTIVE_RUNTIME", "insights_tree", secondary
    if rel.startswith("infrastructure/"):
        return "ACTIVE_RUNTIME", "infrastructure_tree", secondary
    if rel.startswith("scripts/"):
        return "ACTIVE_RUNTIME", "repo_script", ["OWNER_REVIEW_REQUIRED"]

    if is_dir:
        return "OWNER_REVIEW_REQUIRED", "directory_unclassified", secondary

    return "OWNER_REVIEW_REQUIRED", "unclassified_significant_path", secondary


def assert_known_classification(name: str) -> None:
    if name not in CLASSIFICATIONS:
        raise ValueError(f"unknown classification: {name}")
