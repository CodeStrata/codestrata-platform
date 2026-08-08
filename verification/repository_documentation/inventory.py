"""Documentation inventory and classification for Slice 16.2."""

from __future__ import annotations

from pathlib import Path

from verification.repository_documentation.models import DocEntry

PRUNE = {
    ".git",
    ".venv",
    "node_modules",
    ".vitepress/dist",
    "__pycache__",
    ".wrangler",
}


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def classify_doc(rel: str) -> tuple[str, str, list[str]]:
    lower = rel.lower()
    secondary: list[str] = []

    if any(
        part in lower
        for part in (
            "/.vitepress/dist/",
            "docs/.vitepress/dist",
            ".export-staging/",
            "/dist/",
        )
    ):
        return "GENERATED", "generated_or_export_build", ["DELETE_CANDIDATE"]

    if rel.startswith(".export-staging/"):
        return "EXPORT_ONLY", "export_staging", secondary

    if rel == "ROADMAP.md" or "archive candidate" in lower:
        return "ARCHIVE_CANDIDATE", "roadmap_or_marked_archive", ["HISTORICAL"]

    if rel.startswith("docs/platform/") or rel == "docs/platform":
        return "ARCHIVE_CANDIDATE", "unpublished_platform_docs", ["STALE", "HISTORICAL"]

    if rel.startswith("docs/internal/") or rel == "docs/internal":
        return "HISTORICAL", "internal_unpublished", ["ARCHIVE_CANDIDATE"]

    if rel == "docs/community/vs-platform.md":
        return "ACTIVE", "boundary_page_excluded_from_publish", ["OWNER_REVIEW_REQUIRED"]

    if rel.startswith("platform/docs/"):
        if "repository-cleanup" in rel:
            return "ACTIVE", "cleanup_guide_internal", secondary
        return "ACTIVE", "platform_internal_docs", ["OWNER_REVIEW_REQUIRED"]

    if rel.startswith("docs/") and rel.endswith(".md"):
        # Meta docs at docs root often maintainer-facing
        name = Path(rel).name
        if name in {
            "MIGRATION_PLAN.md",
            "EXTRACTION.md",
            "WEBSITE_STYLE_ALIGNMENT.md",
            "VISUAL_REGRESSION.md",
            "DEPLOYMENT.md",
            "CI.md",
        }:
            return "ACTIVE", "docs_maintainer_meta", ["OWNER_REVIEW_REQUIRED"]
        if rel.startswith(
            (
                "docs/getting-started/",
                "docs/engine/",
                "docs/assessments/",
                "docs/reports/",
                "docs/extensions/",
                "docs/ai-providers/",
                "docs/reference/",
                "docs/security/",
                "docs/troubleshooting/",
                "docs/faq/",
                "docs/community/",
            )
        ) or rel in {"docs/index.md", "docs/README.md", "docs/ARCHITECTURE.md", "docs/CONTRIBUTING.md", "docs/SECURITY.md", "docs/PRIVACY.md", "docs/SUPPORT.md"}:
            return "ACTIVE", "community_docs", secondary
        return "OWNER_REVIEW_REQUIRED", "docs_unclassified", secondary

    if rel.startswith("engine/docs/"):
        return "ACTIVE", "engine_maintainer_docs", secondary

    if rel.startswith("design-system/documentation/"):
        return "ACTIVE", "design_system_docs", secondary

    if rel.startswith("knowledge/"):
        return "ACTIVE", "engineering_knowledge", secondary

    if rel.startswith("examples/") and rel.endswith(".md"):
        return "ACTIVE", "examples_docs", secondary

    if rel.startswith("vscode-plugin/"):
        if "/out/" in lower or "/.vscode-test/" in lower:
            return "GENERATED", "vscode_generated", ["DELETE_CANDIDATE"]
        return "ACTIVE", "vscode_docs", secondary

    if rel.startswith("insights/"):
        return "ACTIVE", "insights_internal_docs", ["OWNER_REVIEW_REQUIRED"]

    if rel.startswith("verification/") and rel.endswith("README.md"):
        return "ACTIVE", "verification_readme", ["HISTORICAL"]

    if rel in {
        "README.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "ARCHITECTURE.md",
        "CHANGELOG.md",
    }:
        return "ACTIVE", "root_authority_or_pointer", secondary

    if "changelog" in lower:
        return "ACTIVE", "changelog", secondary

    return "OWNER_REVIEW_REQUIRED", "unclassified_doc", secondary


def iter_markdown_files(monorepo: Path) -> list[str]:
    found: list[str] = []
    roots = [
        monorepo / "README.md",
        monorepo / "SECURITY.md",
        monorepo / "CONTRIBUTING.md",
        monorepo / "CODE_OF_CONDUCT.md",
        monorepo / "ARCHITECTURE.md",
        monorepo / "CHANGELOG.md",
        monorepo / "ROADMAP.md",
        monorepo / "docs",
        monorepo / "knowledge",
        monorepo / "examples",
        monorepo / "platform" / "docs",
        monorepo / "engine" / "docs",
        monorepo / "design-system" / "documentation",
        monorepo / "vscode-plugin",
        monorepo / "insights" / "docs",
        monorepo / "insights" / "README.md",
    ]
    # verification READMEs (shallow)
    ver = monorepo / "verification"
    if ver.is_dir():
        for child in sorted(ver.iterdir()):
            readme = child / "README.md"
            if readme.is_file():
                found.append(_rel(monorepo, readme))

    for root in roots:
        if root.is_file() and root.suffix.lower() in {".md", ".mdx"}:
            found.append(_rel(monorepo, root))
            continue
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".mdx"}:
                continue
            rel = _rel(monorepo, path)
            parts = set(Path(rel).parts)
            if parts & PRUNE:
                continue
            if "node_modules" in rel or ".vitepress/dist" in rel or ".vscode-test" in rel:
                continue
            if rel.startswith("vscode-plugin/out/"):
                continue
            found.append(rel)

    return sorted(set(found))


def build_doc_inventory(monorepo: Path) -> list[DocEntry]:
    entries: list[DocEntry] = []
    for rel in iter_markdown_files(monorepo):
        primary, notes, secondary = classify_doc(rel)
        # Strengthen archive marking when banner present
        path = monorepo / rel
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
        except OSError:
            text = ""
        lower_text = text.lower()
        if "archive" in lower_text and "slice 16.2" in lower_text:
            if primary == "ACTIVE" and rel.startswith("docs/platform/"):
                primary = "ARCHIVE_CANDIDATE"
                notes = "banner_archive"
        if "internal (slice 16.2)" in lower_text and rel.startswith("platform/docs/"):
            notes = notes or "internal_banner"
        entries.append(
            DocEntry(
                path=rel,
                classification=primary,
                notes=notes,
                secondary=sorted(set(secondary)),
            )
        )
    return entries
