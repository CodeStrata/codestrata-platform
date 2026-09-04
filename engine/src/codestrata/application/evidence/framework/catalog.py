"""Versioned evidence-pack catalog and repository-aware recommendations."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from codestrata.domain.evidence.framework.models import (
    EvidenceActivity,
    EvidenceCatalog,
    EvidenceFamily,
    EvidencePackActivity,
    EvidencePackManifest,
    EvidencePackRecommendation,
    EvidencePlan,
)

_LANGUAGE_SUFFIXES = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".php": "php",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
}


def detect_repository_languages(repository: Path, *, max_files: int = 10_000) -> tuple[str, ...]:
    """Return stable language hints without reading source text."""

    root = repository.expanduser().resolve()
    detected: set[str] = set()
    seen = 0
    if not root.is_dir():
        return ()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(
            part in {".git", "node_modules", ".venv", "dist", "build"} for part in relative.parts
        ):
            continue
        seen += 1
        language = _LANGUAGE_SUFFIXES.get(path.suffix.lower())
        if language:
            detected.add(language)
        if seen >= max_files:
            break
    return tuple(sorted(detected))


class EvidencePackRegistry:
    """Resolves packs into explicit activities; packs are never inert labels."""

    def __init__(self, manifests: tuple[EvidencePackManifest, ...] | None = None) -> None:
        values = manifests or default_pack_manifests()
        self._packs = {item.key: item for item in values}
        self._aliases = {item.pack_id: item.key for item in values}

    def manifests(self) -> tuple[EvidencePackManifest, ...]:
        return tuple(self._packs[key] for key in sorted(self._packs))

    def resolve(self, selection: str) -> EvidencePackManifest:
        key = self._aliases.get(selection, selection)
        try:
            return self._packs[key]
        except KeyError as error:
            known = ", ".join(sorted(self._packs))
            raise ValueError(
                f"unknown evidence pack {selection!r}; available packs: {known}"
            ) from error

    def expand(self, selections: tuple[str, ...]) -> tuple[EvidencePackManifest, ...]:
        ordered: list[EvidencePackManifest] = []
        visited: set[str] = set()

        def visit(selection: str) -> None:
            manifest = self.resolve(selection)
            if manifest.key in visited:
                return
            for included in manifest.includes:
                visit(included)
            visited.add(manifest.key)
            ordered.append(manifest)

        for selection in selections:
            visit(selection)
        return tuple(ordered)

    def apply(
        self,
        plan: EvidencePlan,
        *,
        selections: tuple[str, ...],
        registry: object,
        repository: Path,
    ) -> EvidencePlan:
        """Replace pack-owned activities with the selected pack composition."""

        from codestrata.application.evidence.framework.collectors import (
            CollectorContext,
            CollectorRegistry,
        )

        assert isinstance(registry, CollectorRegistry)
        expanded = self.expand(selections)
        pack_collector_ids = {
            template.collector_id for pack in self.manifests() for template in pack.activities
        }
        activities = [
            activity
            for activity in plan.activities
            if activity.collector_id not in pack_collector_ids
        ]
        by_collector = {activity.collector_id for activity in activities}
        working = plan.model_copy(update={"activities": tuple(activities)})
        for pack in expanded:
            for template in pack.activities:
                if template.collector_id in by_collector:
                    continue
                collector = registry.get(template.collector_id)
                activity = EvidenceActivity(
                    activity_id=template.activity_id,
                    collector_id=template.collector_id,
                    configuration=dict(template.configuration),
                )
                context = CollectorContext(
                    plan=working,
                    activity=activity,
                    repository=repository,
                    run_id="pack-preview",
                )
                available, _ = collector.available()
                applicable, _ = collector.applicable(context)
                if not template.required and not available:
                    continue
                if template.when_applicable and not applicable:
                    continue
                activities.append(activity)
                by_collector.add(template.collector_id)
                working = working.model_copy(update={"activities": tuple(activities)})
        return working.model_copy(
            update={
                "packs": tuple(self.resolve(selection).key for selection in selections),
                "activities": tuple(activities),
            }
        )


def default_pack_manifests() -> tuple[EvidencePackManifest, ...]:
    return (
        EvidencePackManifest(
            pack_id="repository-baseline",
            version="1.0",
            title="Repository baseline",
            description="Inventory, declared dependencies, and observable testing structure.",
            goal="Establish what the repository contains and where evidence is incomplete.",
            families=(
                EvidenceFamily.REPOSITORY,
                EvidenceFamily.DEPENDENCIES,
                EvidenceFamily.TESTING,
            ),
            activities=(
                EvidencePackActivity(
                    activity_id="inventory", collector_id="codestrata.repository-inventory"
                ),
                EvidencePackActivity(
                    activity_id="dependencies", collector_id="codestrata.dependency-declarations"
                ),
                EvidencePackActivity(
                    activity_id="testing", collector_id="codestrata.testing-structure"
                ),
            ),
        ),
        EvidencePackManifest(
            pack_id="language-intelligence",
            version="1.0",
            title="Language structure",
            description=(
                "Selects applicable Python, Java, JavaScript/TypeScript, PHP, "
                "and C# evidence providers."
            ),
            goal=(
                "Map source units, imports, layers, frameworks, and test "
                "classification by language."
            ),
            families=(EvidenceFamily.LANGUAGE, EvidenceFamily.ARCHITECTURE),
            recommended_languages=("python", "java", "javascript", "typescript", "php", "csharp"),
            activities=(
                EvidencePackActivity(
                    activity_id="language-python",
                    collector_id="language.python.core",
                    required=False,
                ),
                EvidencePackActivity(
                    activity_id="language-java",
                    collector_id="language.java.core",
                    required=False,
                ),
                EvidencePackActivity(
                    activity_id="language-javascript",
                    collector_id="language.javascript.core",
                    required=False,
                ),
                EvidencePackActivity(
                    activity_id="language-php",
                    collector_id="language.php.core",
                    required=False,
                ),
                EvidencePackActivity(
                    activity_id="language-csharp",
                    collector_id="language.csharp.core",
                    required=False,
                ),
            ),
        ),
        EvidencePackManifest(
            pack_id="code-health",
            version="1.0",
            title="Code health",
            description=(
                "Typed structural biomarkers, with RepoWise enrichment when its "
                "local CLI is installed."
            ),
            goal=(
                "Locate concrete maintainability risks while retaining measurements, "
                "thresholds, and coverage."
            ),
            families=(EvidenceFamily.CODE_HEALTH,),
            recommended_languages=(
                "python",
                "java",
                "php",
                "csharp",
                "javascript",
                "typescript",
                "go",
                "rust",
                "ruby",
            ),
            activities=(
                EvidencePackActivity(
                    activity_id="structural-health", collector_id="codestrata.structural-health"
                ),
                EvidencePackActivity(
                    activity_id="repowise-health",
                    collector_id="external.repowise-health",
                    required=False,
                ),
            ),
            limitations=(
                "The native structural biomarkers are decision aids, not an "
                "empirically calibrated universal score.",
                "RepoWise enrichment requires a separately installed AGPL-3.0 "
                "or commercially licensed executable.",
            ),
        ),
        EvidencePackManifest(
            pack_id="security-quality",
            version="1.0",
            title="Security and quality imports",
            description=(
                "Adds available repository scanners and accepts SARIF from "
                "meta-linters and CI tools."
            ),
            goal="Normalize security, lint, and policy findings into the same traceable report.",
            families=(EvidenceFamily.SECURITY, EvidenceFamily.IMPORTED),
            activities=(
                EvidencePackActivity(
                    activity_id="trivy",
                    collector_id="external.trivy",
                    configuration={"scanners": ["misconfig"]},
                    required=False,
                ),
            ),
            limitations=(
                "SARIF artifact paths are configured separately because they are "
                "repository-specific.",
            ),
        ),
        EvidencePackManifest(
            pack_id="decision-ready-review",
            version="1.0",
            title="Decision-ready engineering review",
            description=(
                "Composes the baseline, applicable language structure, code health, "
                "and available quality scanners."
            ),
            goal=(
                "Produce the broadest local evidence portfolio with explicit gaps "
                "and prioritized action."
            ),
            families=(
                EvidenceFamily.REPOSITORY,
                EvidenceFamily.LANGUAGE,
                EvidenceFamily.ARCHITECTURE,
                EvidenceFamily.CODE_HEALTH,
                EvidenceFamily.DEPENDENCIES,
                EvidenceFamily.TESTING,
                EvidenceFamily.SECURITY,
            ),
            includes=(
                "repository-baseline@1.0",
                "language-intelligence@1.0",
                "code-health@1.0",
                "security-quality@1.0",
            ),
            activities=(),
        ),
    )


def build_catalog(
    repository: Path, *, registry: object, packs: EvidencePackRegistry
) -> EvidenceCatalog:
    from codestrata.application.evidence.framework.collectors import CollectorRegistry

    assert isinstance(registry, CollectorRegistry)
    languages = detect_repository_languages(repository)
    recommendations: list[EvidencePackRecommendation] = []
    for pack in packs.manifests():
        language_match = bool(set(pack.recommended_languages) & set(languages))
        if pack.pack_id == "repository-baseline":
            status: Literal["recommended", "available", "unavailable"] = "recommended"
            reason = "A provenance and coverage baseline is recommended for every repository."
        elif language_match:
            status = "recommended"
            matched = sorted(set(pack.recommended_languages) & set(languages))
            reason = f"Matches detected languages: {', '.join(matched)}."
        else:
            status = "available"
            reason = "Available for explicit selection."
        recommendations.append(EvidencePackRecommendation(pack=pack, status=status, reason=reason))
    return EvidenceCatalog(
        detected_languages=languages,
        collectors=registry.manifests(),
        packs=tuple(recommendations),
    )
