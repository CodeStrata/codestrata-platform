"""Collector SDK, registry, and high-leverage built-in repository collectors."""

from __future__ import annotations

import fnmatch
import json
import re
import shutil
import subprocess
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from codestrata.application.evidence.dependency.paths import classify_manifest_basename
from codestrata.application.evidence.dependency.service import DependencyEvidenceService
from codestrata.application.evidence.framework.sanitization import (
    sanitize_evidence_payload,
)
from codestrata.application.evidence.language.complexity.service import (
    ComplexityEvidenceService,
)
from codestrata.application.evidence.language.factory import (
    create_language_evidence_registry,
)
from codestrata.application.evidence.repository_testing.service import (
    RepositoryTestingEvidenceService,
)
from codestrata.config.settings import (
    DependencyEvidenceSettings,
    RepositoryTestingEvidenceSettings,
)
from codestrata.domain.evidence.framework.models import (
    CollectorManifest,
    CollectorMaturity,
    CostClass,
    Coverage,
    CoverageState,
    EvidenceActivity,
    EvidenceEnvelope,
    EvidenceFamily,
    EvidenceLocation,
    EvidencePlan,
    ExternalAccess,
)
from codestrata.domain.evidence.language.contracts import LanguageEvidenceContext


@dataclass(frozen=True)
class CollectorContext:
    plan: EvidencePlan
    activity: EvidenceActivity
    repository: Path
    run_id: str


@dataclass(frozen=True)
class CollectedRawArtifact:
    """Native collector output that the run workspace must retain by hash."""

    content: bytes
    media_type: str


@dataclass(frozen=True)
class CollectionResult:
    evidence: tuple[EvidenceEnvelope, ...]
    coverage: Coverage
    diagnostics: tuple[str, ...] = ()
    raw_artifacts: tuple[CollectedRawArtifact, ...] = ()


class EvidenceCollector(Protocol):
    manifest: CollectorManifest

    def available(self) -> tuple[bool, str]: ...

    def applicable(self, context: CollectorContext) -> tuple[bool, str]: ...

    def collect(self, context: CollectorContext) -> CollectionResult: ...


class CollectorRegistry:
    """Fail-closed registry that has no dependency on assessment or reporting."""

    def __init__(self, collectors: Iterable[EvidenceCollector]) -> None:
        self._collectors: dict[str, EvidenceCollector] = {}
        for collector in collectors:
            collector_id = collector.manifest.collector_id
            if collector_id in self._collectors:
                raise ValueError(f"duplicate collector ID: {collector_id}")
            self._collectors[collector_id] = collector

    def get(self, collector_id: str) -> EvidenceCollector:
        try:
            return self._collectors[collector_id]
        except KeyError as error:
            raise KeyError(f"unknown collector: {collector_id}") from error

    def manifests(self) -> tuple[CollectorManifest, ...]:
        return tuple(
            collector.manifest
            for collector in sorted(
                self._collectors.values(), key=lambda item: item.manifest.collector_id
            )
        )


class _AvailableCollector:
    def available(self) -> tuple[bool, str]:
        return True, "Built into CodeStrata."

    def applicable(self, context: CollectorContext) -> tuple[bool, str]:
        if not context.repository.is_dir():
            return False, "Repository path is not a directory."
        return True, "Repository path is readable."


_LANGUAGE_SUFFIXES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".php": "PHP",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".c": "C",
    ".h": "C/C++",
    ".cpp": "C++",
    ".cc": "C++",
}

_MANIFEST_NAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "poetry.lock",
    "uv.lock",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "composer.lock",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "Cargo.lock",
    "Gemfile",
    "Gemfile.lock",
    "packages.config",
    "packages.lock.json",
    "Directory.Packages.props",
}
_MANIFEST_NAMES_LOWER = frozenset(item.lower() for item in _MANIFEST_NAMES)

_TOOL_CONFIGS = {
    ".pre-commit-config.yaml": "pre-commit",
    ".pre-commit-config.yml": "pre-commit",
    ".trunk/trunk.yaml": "trunk-check",
    ".trunk/trunk.yml": "trunk-check",
    ".mega-linter.yml": "megalinter",
    ".megalinter.yml": "megalinter",
}


def _is_selected(path: str, plan: EvidencePlan) -> bool:
    included = any(
        fnmatch.fnmatch(path, pattern) or (pattern == "**/*" and "/" not in path)
        for pattern in plan.scope.include
    )
    excluded = any(fnmatch.fnmatch(path, pattern) for pattern in plan.scope.exclude)
    return included and not excluded


def _is_dependency_artifact(path: str) -> bool:
    name = Path(path).name
    lower = name.lower()
    return (
        name in _MANIFEST_NAMES
        or lower in _MANIFEST_NAMES_LOWER
        or (lower.startswith("requirements") and lower.endswith(".txt"))
        or lower.endswith((".csproj", ".fsproj", ".vbproj"))
    )


def _repository_files(context: CollectorContext) -> tuple[list[str], bool]:
    files: list[str] = []
    truncated = False
    for path in sorted(context.repository.rglob("*")):
        if not path.is_file():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(context.repository):
            continue
        relative = path.relative_to(context.repository).as_posix()
        if not _is_selected(relative, context.plan):
            continue
        files.append(relative)
        if len(files) >= context.plan.limits.max_files:
            truncated = True
            break
    return files, truncated


def _read_bounded(
    repository: Path,
    paths: Iterable[str],
    *,
    max_file_bytes: int,
) -> tuple[dict[str, str], dict[str, str]]:
    texts: dict[str, str] = {}
    errors: dict[str, str] = {}
    for relative in paths:
        path = repository / relative
        try:
            if path.stat().st_size > max_file_bytes:
                errors[relative] = "file_too_large"
                continue
            texts[relative] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors[relative] = "unsupported_encoding"
        except OSError:
            errors[relative] = "read_failed"
    return texts, errors


def repository_revision(repository: Path) -> str:
    """Resolve a revision without failing non-git repository workflows."""

    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        dirty = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                ".",
                ":(exclude).codestrata-artifacts",
                ":(exclude).codestrata-artifacts/**",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        return f"{head}+dirty" if dirty else head
    except (OSError, subprocess.SubprocessError):
        return "working-tree"


class RepositoryInventoryCollector(_AvailableCollector):
    manifest = CollectorManifest(
        collector_id="codestrata.repository-inventory",
        version="1.0.0",
        label="Repository inventory",
        description=(
            "Inventories files, language hints, manifests, revision, and existing "
            "quality-tool orchestration without copying source text."
        ),
        output_kinds=("repository.inventory",),
        coverage_semantics="Files selected by the plan scope, bounded by max_files.",
        limitations=(
            "Languages are inferred from file extensions.",
            "A detected tool configuration does not prove the tool is run or passing.",
        ),
        family=EvidenceFamily.REPOSITORY,
        capability_ids=("repository.files", "repository.languages", "repository.tooling"),
    )

    def collect(self, context: CollectorContext) -> CollectionResult:
        files, truncated = _repository_files(context)
        languages = Counter(
            language
            for relative in files
            if (language := _LANGUAGE_SUFFIXES.get(Path(relative).suffix.lower()))
        )
        manifests = tuple(relative for relative in files if _is_dependency_artifact(relative))
        tools = tuple(
            {"tool": tool, "configuration_path": path}
            for path, tool in sorted(_TOOL_CONFIGS.items())
            if path in files
        )
        coverage = Coverage(
            state=CoverageState.PARTIAL if truncated else CoverageState.COMPLETE,
            population="Files included by the evidence plan scope.",
            planned=len(files) if not truncated else context.plan.limits.max_files,
            examined=len(files),
            successful=True,
            supports_absence_conclusion=not truncated,
            limitations=("File limit reached; inventory is truncated.",) if truncated else (),
        )
        payload: dict[str, Any] = {
            "file_count": len(files),
            "languages": dict(sorted(languages.items())),
            "manifests": manifests,
            "quality_orchestration": tools,
            "revision_observed": repository_revision(context.repository),
            "source_text_stored": False,
        }
        evidence = EvidenceEnvelope.create(
            kind="repository.inventory",
            run_id=context.run_id,
            activity_id=context.activity.activity_id,
            collector_id=self.manifest.collector_id,
            collector_version=self.manifest.version,
            repository_id=context.plan.subject.repository_id,
            revision=context.plan.subject.revision,
            method="filesystem inventory and git metadata",
            production_mode="observed",
            coverage=coverage,
            payload=payload,
        )
        return CollectionResult(evidence=(evidence,), coverage=coverage)


class FilePatternCollector(_AvailableCollector):
    manifest = CollectorManifest(
        collector_id="codestrata.file-pattern",
        version="1.0.0",
        label="File and pattern observations",
        description=(
            "Searches user-defined bounded regular expressions and records counts and "
            "locations without retaining matching source text."
        ),
        output_kinds=("source.pattern.search", "source.pattern.occurrence"),
        coverage_semantics="Selected readable text files within plan bounds.",
        limitations=(
            "Text search is not semantic or AST-aware.",
            "Binary, oversized, and unsupported-encoding files are not inspected.",
        ),
        configuration_schema={
            "type": "object",
            "properties": {
                "patterns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id", "regex"],
                        "properties": {
                            "id": {"type": "string"},
                            "regex": {"type": "string"},
                            "globs": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                }
            },
        },
        family=EvidenceFamily.REPOSITORY,
        capability_ids=("source.patterns",),
        maturity=CollectorMaturity.PARTIAL,
    )

    def applicable(self, context: CollectorContext) -> tuple[bool, str]:
        ok, reason = super().applicable(context)
        if not ok:
            return ok, reason
        patterns = context.activity.configuration.get("patterns", [])
        if not patterns:
            return False, "No patterns are configured."
        if not isinstance(patterns, list) or len(patterns) > 100:
            raise ValueError("patterns must be an array containing at most 100 entries")
        pattern_ids: list[str] = []
        for raw_pattern in patterns:
            if not isinstance(raw_pattern, Mapping):
                raise ValueError("each pattern must be an object")
            pattern_id = str(raw_pattern.get("id", "")).strip()
            expression = str(raw_pattern.get("regex", "")).strip()
            if not pattern_id or not expression:
                raise ValueError("each pattern requires non-blank id and regex")
            if len(expression) > 500:
                raise ValueError("pattern regex must not exceed 500 characters")
            globs = raw_pattern.get("globs", ["**/*"])
            if not isinstance(globs, list) or not globs:
                raise ValueError("pattern globs must be a non-empty array")
            try:
                re.compile(expression)
            except re.error as error:
                raise ValueError(f"invalid regex for pattern {pattern_id!r}: {error}") from error
            pattern_ids.append(pattern_id)
        if len(pattern_ids) != len(set(pattern_ids)):
            raise ValueError("pattern IDs must be unique within an activity")
        return True, f"{len(patterns)} pattern(s) configured."

    def collect(self, context: CollectorContext) -> CollectionResult:
        files, truncated = _repository_files(context)
        texts, errors = _read_bounded(
            context.repository,
            files,
            max_file_bytes=context.plan.limits.max_file_bytes,
        )
        evidence: list[EvidenceEnvelope] = []
        searched_pairs = 0
        record_limit_reached = False
        patterns = context.activity.configuration.get("patterns", [])
        for raw_pattern in patterns:
            if len(evidence) >= context.plan.limits.max_evidence_records:
                record_limit_reached = True
                break
            if not isinstance(raw_pattern, Mapping):
                raise ValueError("each pattern must be an object")
            pattern_id = str(raw_pattern.get("id", "")).strip()
            expression = str(raw_pattern.get("regex", "")).strip()
            if not pattern_id or not expression:
                raise ValueError("each pattern requires non-blank id and regex")
            compiled = re.compile(expression)
            globs = tuple(str(item) for item in raw_pattern.get("globs", ("**/*",)))
            occurrences: list[tuple[str, int]] = []
            searched = 0
            occurrences_truncated = False
            occurrence_limit = context.plan.limits.max_evidence_records - len(evidence) - 1
            for relative, text in texts.items():
                if not any(
                    fnmatch.fnmatch(relative, item) or (item == "**/*" and "/" not in relative)
                    for item in globs
                ):
                    continue
                searched += 1
                searched_pairs += 1
                for line_number, line in enumerate(text.splitlines(), start=1):
                    if compiled.search(line):
                        if len(occurrences) >= occurrence_limit:
                            occurrences_truncated = True
                            record_limit_reached = True
                            break
                        occurrences.append((relative, line_number))
                if occurrences_truncated:
                    break
            complete = not truncated and not errors and not occurrences_truncated
            coverage = Coverage(
                state=CoverageState.COMPLETE if complete else CoverageState.PARTIAL,
                population=f"Text files matching globs for pattern {pattern_id!r}.",
                planned=searched + len(errors),
                examined=searched,
                successful=True,
                supports_absence_conclusion=complete,
                limitations=tuple(
                    item
                    for item in (
                        "Repository file limit reached." if truncated else "",
                        f"{len(errors)} file(s) could not be read." if errors else "",
                        (
                            "Evidence-record limit reached; occurrence locations are truncated."
                            if occurrences_truncated
                            else ""
                        ),
                    )
                    if item
                ),
            )
            summary = EvidenceEnvelope.create(
                kind="source.pattern.search",
                run_id=context.run_id,
                activity_id=context.activity.activity_id,
                collector_id=self.manifest.collector_id,
                collector_version=self.manifest.version,
                repository_id=context.plan.subject.repository_id,
                revision=context.plan.subject.revision,
                method="bounded regular-expression search",
                production_mode="observed",
                coverage=coverage,
                payload={
                    "pattern_id": pattern_id,
                    "regex": expression,
                    "globs": globs,
                    "assertion": "present" if occurrences else "absent",
                    "occurrence_count": len(occurrences),
                    "occurrence_count_is_lower_bound": occurrences_truncated,
                    "source_text_stored": False,
                },
            )
            evidence.append(summary)
            for relative, line_number in occurrences:
                evidence.append(
                    EvidenceEnvelope.create(
                        kind="source.pattern.occurrence",
                        run_id=context.run_id,
                        activity_id=context.activity.activity_id,
                        collector_id=self.manifest.collector_id,
                        collector_version=self.manifest.version,
                        repository_id=context.plan.subject.repository_id,
                        revision=context.plan.subject.revision,
                        method="bounded regular-expression search",
                        production_mode="observed",
                        coverage=coverage,
                        payload={"pattern_id": pattern_id, "source_text_stored": False},
                        locations=(EvidenceLocation(path=relative, start_line=line_number),),
                        parent_evidence_ids=(summary.evidence_id,),
                    )
                )
        aggregate = Coverage(
            state=(
                CoverageState.PARTIAL
                if truncated or errors or record_limit_reached
                else CoverageState.COMPLETE
            ),
            population="Configured pattern and selected-file pairs.",
            planned=searched_pairs + len(errors),
            examined=searched_pairs,
            successful=True,
            limitations=tuple(
                item
                for item in (
                    f"{len(errors)} unreadable file(s)." if errors else "",
                    ("Evidence-record limit reached." if record_limit_reached else ""),
                )
                if item
            ),
        )
        return CollectionResult(
            evidence=tuple(evidence),
            coverage=aggregate,
            diagnostics=tuple(f"{path}: {reason}" for path, reason in sorted(errors.items())),
        )


class DependencyCollectorAdapter(_AvailableCollector):
    manifest = CollectorManifest(
        collector_id="codestrata.dependency-declarations",
        version="1.0.0",
        label="Dependency declarations",
        description="Wraps CodeStrata 0.2.0 typed dependency evidence collectors.",
        output_kinds=("repository.dependencies",),
        cost_class=CostClass.MEDIUM,
        coverage_semantics=(
            "Recognized dependency manifests and lockfiles, with typed parsing coverage "
            "declared separately."
        ),
        limitations=(
            "Declared dependencies are not proof of deployed components.",
            "No vulnerability, license, or reachability conclusion is made.",
            "Some ecosystems and lockfile formats are detected but not yet typed-parsed.",
        ),
        family=EvidenceFamily.DEPENDENCIES,
        capability_ids=("dependencies.declared", "dependencies.lockfiles"),
    )

    def applicable(self, context: CollectorContext) -> tuple[bool, str]:
        ok, reason = super().applicable(context)
        if not ok:
            return ok, reason
        files, _truncated = _repository_files(context)
        count = sum(_is_dependency_artifact(path) for path in files)
        if not count:
            return False, "No recognized dependency manifest or lockfile is in plan scope."
        return True, f"{count} dependency manifest or lockfile artifact(s) discovered."

    def collect(self, context: CollectorContext) -> CollectionResult:
        files, truncated = _repository_files(context)
        dependency_paths = [path for path in files if _is_dependency_artifact(path)]
        manifest_paths = [
            path for path in dependency_paths if classify_manifest_basename(path) is not None
        ]
        unsupported_paths = sorted(set(dependency_paths) - set(manifest_paths))
        texts, errors = _read_bounded(
            context.repository,
            manifest_paths,
            max_file_bytes=context.plan.limits.max_file_bytes,
        )
        service = DependencyEvidenceService(
            DependencyEvidenceSettings(
                enabled=True,
                max_files=context.plan.limits.max_files,
                max_file_chars=context.plan.limits.max_file_bytes,
            )
        )
        bundle = service.collect(
            repository_id=context.plan.subject.repository_id,
            relative_paths=files,
            file_texts=texts,
            configuration_fingerprint=context.plan.plan_id,
        )
        counters = bundle.coverage
        complete = (
            not truncated
            and not errors
            and counters.manifests_failed == 0
            and counters.manifests_partially_parsed == 0
            and not unsupported_paths
        )
        limitations = ["Dependencies are declarations only; runtime resolution was not executed."]
        if unsupported_paths:
            limitations.append(
                f"Typed parsing is unavailable for {len(unsupported_paths)} "
                f"artifact(s): {', '.join(unsupported_paths[:10])}."
            )
        coverage = Coverage(
            state=CoverageState.COMPLETE if complete else CoverageState.PARTIAL,
            population="Recognized dependency manifests and lockfiles in plan scope.",
            planned=len(dependency_paths),
            examined=counters.manifests_parsed,
            successful=counters.manifests_failed == 0,
            supports_absence_conclusion=complete,
            limitations=tuple(limitations),
        )
        locations = tuple(EvidenceLocation(path=item.path) for item in bundle.manifests)
        bundle_payload = bundle.model_dump(mode="json")
        bundle_payload["discovered_dependency_artifacts"] = dependency_paths
        bundle_payload["unsupported_dependency_artifacts"] = unsupported_paths
        sanitized_payload, redactions = sanitize_evidence_payload(
            bundle_payload, context.plan.sensitivity
        )
        evidence = EvidenceEnvelope.create(
            kind="repository.dependencies",
            run_id=context.run_id,
            activity_id=context.activity.activity_id,
            collector_id=self.manifest.collector_id,
            collector_version=self.manifest.version,
            repository_id=context.plan.subject.repository_id,
            revision=context.plan.subject.revision,
            method="CodeStrata typed manifest parsing",
            production_mode="observed",
            coverage=coverage,
            payload=sanitized_payload,
            locations=locations,
            redactions=redactions,
        )
        return CollectionResult(
            evidence=(evidence,),
            coverage=coverage,
            diagnostics=tuple(bundle.diagnostics),
        )


class TestingStructureCollectorAdapter(_AvailableCollector):
    manifest = CollectorManifest(
        collector_id="codestrata.testing-structure",
        version="1.0.0",
        label="Testing structure",
        description="Wraps CodeStrata 0.2.0 repository-observable testing evidence.",
        output_kinds=("repository.testing-structure",),
        cost_class=CostClass.MEDIUM,
        coverage_semantics="Discovered testing candidates and supported configurations.",
        limitations=(
            "Test presence is not proof that tests pass or provide adequate coverage.",
            "Runtime tests are not executed.",
        ),
        family=EvidenceFamily.TESTING,
        capability_ids=("tests.presence", "tests.configuration", "tests.relationships"),
    )

    def collect(self, context: CollectorContext) -> CollectionResult:
        files, truncated = _repository_files(context)
        texts, errors = _read_bounded(
            context.repository,
            files,
            max_file_bytes=context.plan.limits.max_file_bytes,
        )
        service = RepositoryTestingEvidenceService(
            RepositoryTestingEvidenceSettings(
                enabled=True,
                max_files=context.plan.limits.max_files,
                max_file_chars=context.plan.limits.max_file_bytes,
                max_file_bytes=context.plan.limits.max_file_bytes,
            )
        )
        bundle = service.collect(
            repository_id=context.plan.subject.repository_id,
            relative_paths=files,
            file_texts=texts,
            load_errors=errors,
            configuration_fingerprint=context.plan.plan_id,
        )
        counters = bundle.coverage
        complete = not truncated and counters.skipped_files == 0
        coverage = Coverage(
            state=CoverageState.COMPLETE if complete else CoverageState.PARTIAL,
            population="Repository-observable test candidates and configurations.",
            planned=counters.candidate_test_files_discovered,
            examined=counters.candidate_files_inspected,
            successful=True,
            supports_absence_conclusion=False,
            limitations=tuple(item.summary for item in bundle.limitations),
        )
        locations = tuple(EvidenceLocation(path=item.path) for item in bundle.file_candidates)
        sanitized_payload, redactions = sanitize_evidence_payload(
            bundle.model_dump(mode="json"), context.plan.sensitivity
        )
        evidence = EvidenceEnvelope.create(
            kind="repository.testing-structure",
            run_id=context.run_id,
            activity_id=context.activity.activity_id,
            collector_id=self.manifest.collector_id,
            collector_version=self.manifest.version,
            repository_id=context.plan.subject.repository_id,
            revision=context.plan.subject.revision,
            method="CodeStrata typed testing-structure inspection",
            production_mode="observed",
            coverage=coverage,
            payload=sanitized_payload,
            locations=locations,
            redactions=redactions,
        )
        return CollectionResult(evidence=(evidence,), coverage=coverage)


class LanguageProviderCollectorAdapter(_AvailableCollector):
    """Expose one existing language provider through the isolated collector SDK."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        metadata = provider.metadata
        capabilities = tuple(sorted(metadata.capabilities.supported_ids()))
        limitations = tuple(
            item.limitations for item in metadata.capabilities.supported if item.limitations
        )
        self.manifest = CollectorManifest(
            collector_id=str(metadata.provider_id),
            version=metadata.provider_version,
            label=metadata.title,
            description=metadata.description,
            output_kinds=(
                "language.provider-summary",
                "language.source-unit",
                "language.dependency",
                "language.framework-usage",
            ),
            cost_class=CostClass.MEDIUM,
            coverage_semantics=(
                "Source files matching the provider language and selected plan scope."
            ),
            limitations=limitations,
            configuration_schema={
                "type": "object",
                "properties": {
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(capabilities)},
                        "default": list(capabilities),
                    }
                },
            },
            family=EvidenceFamily.LANGUAGE,
            languages=tuple(metadata.supported_languages),
            capability_ids=capabilities,
            maturity=CollectorMaturity.PARTIAL,
            recommendation_weight=85,
        )

    def _context(
        self, context: CollectorContext, *, include_text: bool
    ) -> tuple[LanguageEvidenceContext, tuple[str, ...], dict[str, str]]:
        files, _ = _repository_files(context)
        texts: dict[str, str] = {}
        errors: dict[str, str] = {}
        if include_text:
            texts, errors = _read_bounded(
                context.repository,
                files,
                max_file_bytes=context.plan.limits.max_file_bytes,
            )
        provider_context = LanguageEvidenceContext(
            repository_id=context.plan.subject.repository_id,
            relative_paths=tuple(files),
            file_texts=texts,
            detected_languages=tuple(self.manifest.languages),
            configuration={"fingerprint": context.plan.plan_id},
        )
        return provider_context, tuple(files), errors

    def applicable(self, context: CollectorContext) -> tuple[bool, str]:
        ok, reason = super().applicable(context)
        if not ok:
            return ok, reason
        provider_context, _, _ = self._context(context, include_text=False)
        applicability = self.provider.evaluate_applicability(provider_context)
        return applicability.is_applicable, (
            f"Applicable to {', '.join(self.manifest.languages)} source files."
            if applicability.is_applicable
            else applicability.message or "No matching language source files."
        )

    def collect(self, context: CollectorContext) -> CollectionResult:
        provider_context, files, errors = self._context(context, include_text=True)
        selected_raw = context.activity.configuration.get(
            "capabilities", list(self.manifest.capability_ids)
        )
        if not isinstance(selected_raw, list):
            raise ValueError("language capabilities must be an array")
        selected = tuple(dict.fromkeys(str(item) for item in selected_raw))
        unknown = sorted(set(selected) - set(self.manifest.capability_ids))
        if unknown:
            raise ValueError(f"unsupported language capabilities: {', '.join(unknown)}")
        result = self.provider.collect(provider_context)
        if result.bundle is None:
            raise RuntimeError(result.message or "language provider produced no evidence bundle")
        bundle = result.bundle
        file_coverage = bundle.coverage.file_coverage
        planned = file_coverage.inputs_considered if file_coverage else len(files)
        examined = file_coverage.inputs_analyzed if file_coverage else len(files) - len(errors)
        complete = result.status.value == "succeeded" and not errors and examined >= planned
        coverage = Coverage(
            state=CoverageState.COMPLETE if complete else CoverageState.PARTIAL,
            population=f"{bundle.language} source files selected by the evidence plan.",
            planned=planned,
            examined=examined,
            successful=result.status.value in {"succeeded", "partially_succeeded"},
            supports_absence_conclusion=complete,
            limitations=tuple(
                dict.fromkeys(
                    (*bundle.diagnostics, *(f"{path}: {reason}" for path, reason in errors.items()))
                )
            ),
        )
        summary_payload, summary_redactions = sanitize_evidence_payload(
            {
                "provider_id": bundle.provider_id,
                "provider_version": bundle.provider_version,
                "language": bundle.language,
                "selected_capabilities": selected,
                "source_unit_count": len(bundle.source_units),
                "dependency_count": len(bundle.dependencies),
                "framework_usage_count": len(bundle.framework_usages),
                "provider_coverage": bundle.coverage.model_dump(mode="json"),
            },
            context.plan.sensitivity,
        )
        summary = EvidenceEnvelope.create(
            kind="language.provider-summary",
            run_id=context.run_id,
            activity_id=context.activity.activity_id,
            collector_id=self.manifest.collector_id,
            collector_version=self.manifest.version,
            repository_id=context.plan.subject.repository_id,
            revision=context.plan.subject.revision,
            method="CodeStrata typed language evidence provider",
            production_mode="observed",
            coverage=coverage,
            payload=summary_payload,
            redactions=summary_redactions,
        )
        evidence: list[EvidenceEnvelope] = [summary]
        include_units = any(
            item.startswith(("source.", "architecture.", "tests.")) for item in selected
        )
        include_dependencies = any(item.startswith("dependencies.") for item in selected)
        include_frameworks = any(item.startswith("framework.") for item in selected)

        def add(
            kind: str, payload: dict[str, Any], locations: tuple[EvidenceLocation, ...]
        ) -> None:
            if len(evidence) >= context.plan.limits.max_evidence_records:
                return
            sanitized, redactions = sanitize_evidence_payload(payload, context.plan.sensitivity)
            evidence.append(
                EvidenceEnvelope.create(
                    kind=kind,
                    run_id=context.run_id,
                    activity_id=context.activity.activity_id,
                    collector_id=self.manifest.collector_id,
                    collector_version=self.manifest.version,
                    repository_id=context.plan.subject.repository_id,
                    revision=context.plan.subject.revision,
                    method="CodeStrata typed language evidence provider",
                    production_mode="observed",
                    coverage=coverage,
                    payload=sanitized,
                    locations=locations,
                    parent_evidence_ids=(summary.evidence_id,),
                    redactions=redactions,
                )
            )

        if include_units:
            for item in bundle.source_units:
                add(
                    "language.source-unit",
                    item.model_dump(mode="json"),
                    tuple(EvidenceLocation(path=path) for path in item.paths),
                )
        if include_dependencies:
            for item in bundle.dependencies:
                add(
                    "language.dependency",
                    item.model_dump(mode="json"),
                    tuple(EvidenceLocation(path=path) for path in item.evidence_paths),
                )
        if include_frameworks:
            for item in bundle.framework_usages:
                add(
                    "language.framework-usage",
                    item.model_dump(mode="json"),
                    (EvidenceLocation(path=item.path),),
                )
        limited = len(evidence) >= context.plan.limits.max_evidence_records
        if limited:
            coverage = coverage.model_copy(
                update={
                    "state": CoverageState.PARTIAL,
                    "supports_absence_conclusion": False,
                    "limitations": (*coverage.limitations, "Evidence-record limit reached."),
                }
            )
            evidence = [item.model_copy(update={"coverage": coverage}) for item in evidence]
        return CollectionResult(
            evidence=tuple(evidence),
            coverage=coverage,
            diagnostics=tuple(bundle.diagnostics),
        )


_STRUCTURAL_BIOMARKERS = {
    "large_file": ("physical_line_count", 500, "Split an oversized source file by responsibility."),
    "large_type": (
        "physical_line_count",
        300,
        "Extract cohesive responsibilities from the oversized type.",
    ),
    "long_callable": (
        "physical_line_count",
        60,
        "Extract a named method or helper around one responsibility.",
    ),
    "complex_callable": (
        "branch_point_count",
        10,
        "Simplify branching and isolate decision paths.",
    ),
    "deep_nesting": (
        "max_nesting_depth",
        4,
        "Flatten control flow with guards or extracted helpers.",
    ),
    "parameter_bloat": (
        "parameter_count",
        7,
        "Introduce a cohesive parameter object or narrow the interface.",
    ),
}


def _metric_value(metric: Any) -> int | None:
    return metric.value if getattr(metric.availability, "value", "") == "available" else None


class StructuralHealthCollector(_AvailableCollector):
    """Independent, transparent biomarkers derived from CodeStrata typed facts."""

    manifest = CollectorManifest(
        collector_id="codestrata.structural-health",
        version="1.0.0",
        label="Structural code-health biomarkers",
        description=(
            "Measures file structure across detected languages and typed callable "
            "structure for Python, Java, PHP, and C#; then applies user-selected "
            "transparent thresholds."
        ),
        output_kinds=(
            "code-health.coverage",
            "code-health.measurement",
            "code-health.biomarker",
        ),
        cost_class=CostClass.MEDIUM,
        coverage_semantics=(
            "Selected recognized-language files, with typed callable parsing where supported."
        ),
        limitations=(
            "Structural thresholds are review heuristics, not a universal quality score.",
            "Callable-level typed complexity is currently limited to Python, Java, "
            "PHP, and C#; other languages receive file-level measurements.",
            "Historical churn, ownership, duplication, and runtime behavior require "
            "other collectors.",
        ),
        configuration_schema={
            "type": "object",
            "properties": {
                "biomarkers": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(_STRUCTURAL_BIOMARKERS)},
                    "default": list(_STRUCTURAL_BIOMARKERS),
                },
                "thresholds": {
                    "type": "object",
                    "additionalProperties": {"type": "integer", "minimum": 1},
                },
            },
        },
        family=EvidenceFamily.CODE_HEALTH,
        languages=(
            "python",
            "java",
            "javascript",
            "typescript",
            "php",
            "csharp",
            "go",
            "rust",
            "ruby",
            "kotlin",
            "c",
            "cpp",
        ),
        capability_ids=tuple(f"biomarker.{item}" for item in _STRUCTURAL_BIOMARKERS),
        maturity=CollectorMaturity.PARTIAL,
        recommendation_weight=90,
    )

    def applicable(self, context: CollectorContext) -> tuple[bool, str]:
        ok, reason = super().applicable(context)
        if not ok:
            return ok, reason
        files, _ = _repository_files(context)
        supported = sum(Path(item).suffix.lower() in _LANGUAGE_SUFFIXES for item in files)
        return (
            supported > 0,
            f"{supported} supported source file(s) detected."
            if supported
            else "No recognized source-language files were detected.",
        )

    def collect(self, context: CollectorContext) -> CollectionResult:
        files, truncated = _repository_files(context)
        texts, errors = _read_bounded(
            context.repository,
            files,
            max_file_bytes=context.plan.limits.max_file_bytes,
        )
        selected_raw = context.activity.configuration.get(
            "biomarkers", list(_STRUCTURAL_BIOMARKERS)
        )
        thresholds_raw = context.activity.configuration.get("thresholds", {})
        if not isinstance(selected_raw, list) or not isinstance(thresholds_raw, Mapping):
            raise ValueError("biomarkers must be an array and thresholds must be an object")
        selected = tuple(dict.fromkeys(str(item) for item in selected_raw))
        unknown = sorted(set(selected) - set(_STRUCTURAL_BIOMARKERS))
        if unknown:
            raise ValueError(f"unknown structural biomarkers: {', '.join(unknown)}")
        thresholds: dict[str, int] = {}
        for biomarker_id, (_, default, _) in _STRUCTURAL_BIOMARKERS.items():
            value = int(thresholds_raw.get(biomarker_id, default))
            if value < 1:
                raise ValueError(f"threshold for {biomarker_id} must be positive")
            thresholds[biomarker_id] = value

        aggregate = ComplexityEvidenceService().collect(
            repository_id=context.plan.subject.repository_id,
            relative_paths=files,
            file_texts=texts,
            configuration_fingerprint=context.plan.plan_id,
        )
        typed_paths = {item.path for item in aggregate.files}
        generic_paths = [
            path
            for path in files
            if Path(path).suffix.lower() in _LANGUAGE_SUFFIXES
            and path not in typed_paths
            and path in texts
        ]
        planned = len(typed_paths) + len(generic_paths)
        examined = planned
        failures = sum(item.files_failed for item in aggregate.bundles) + len(errors)
        complete = not truncated and failures == 0 and examined >= planned
        coverage = Coverage(
            state=CoverageState.COMPLETE if complete else CoverageState.PARTIAL,
            population="Supported-language source files selected for structural analysis.",
            planned=planned,
            examined=examined,
            successful=examined > 0,
            supports_absence_conclusion=False,
            limitations=tuple(
                item
                for item in (
                    "Repository file limit reached." if truncated else "",
                    f"{failures} file(s) could not be fully analyzed." if failures else "",
                    *aggregate.diagnostics,
                )
                if item
            ),
        )
        evidence: list[EvidenceEnvelope] = []
        finding_count = 0
        limit_reached = False

        def emit(
            *,
            kind: str,
            payload: dict[str, Any],
            location: EvidenceLocation,
            parents: tuple[str, ...] = (),
        ) -> EvidenceEnvelope | None:
            nonlocal limit_reached
            if len(evidence) >= context.plan.limits.max_evidence_records - 1:
                limit_reached = True
                return None
            envelope = EvidenceEnvelope.create(
                kind=kind,
                run_id=context.run_id,
                activity_id=context.activity.activity_id,
                collector_id=self.manifest.collector_id,
                collector_version=self.manifest.version,
                repository_id=context.plan.subject.repository_id,
                revision=context.plan.subject.revision,
                method="typed structural measurement with explicit user-selected threshold",
                production_mode="derived" if kind == "code-health.biomarker" else "observed",
                coverage=coverage,
                payload=payload,
                locations=(location,),
                parent_evidence_ids=parents,
                confidence_basis=(
                    "Deterministic typed extractor; threshold is recorded in the payload."
                ),
            )
            evidence.append(envelope)
            return envelope

        def measure_and_test(
            *,
            entity_kind: str,
            entity: str,
            language: str,
            path: str,
            line_start: int | None,
            line_end: int | None,
            metrics: dict[str, int | None],
            candidates: tuple[str, ...],
        ) -> None:
            nonlocal finding_count
            location = EvidenceLocation(path=path, start_line=line_start, end_line=line_end)
            measurement = emit(
                kind="code-health.measurement",
                payload={
                    "entity_kind": entity_kind,
                    "entity": entity,
                    "language": language,
                    "metrics": metrics,
                },
                location=location,
            )
            if measurement is None:
                return
            for biomarker_id in candidates:
                if biomarker_id not in selected:
                    continue
                metric_id, _, action = _STRUCTURAL_BIOMARKERS[biomarker_id]
                value = metrics.get(metric_id)
                threshold = thresholds[biomarker_id]
                if value is None or value < threshold:
                    continue
                ratio = value / threshold
                severity = "high" if ratio >= 2 else "medium"
                finding = emit(
                    kind="code-health.biomarker",
                    payload={
                        "biomarker_id": biomarker_id,
                        "entity_kind": entity_kind,
                        "entity": entity,
                        "language": language,
                        "metric_id": metric_id,
                        "value": value,
                        "threshold": threshold,
                        "severity": severity,
                        "reason": (
                            f"{metric_id} is {value}; the selected review threshold is {threshold}."
                        ),
                        "action_title": action,
                        "action_rationale": (
                            "Reduce the measured structural concentration while "
                            "preserving behavior."
                        ),
                        "verification": (
                            f"Re-run this evidence plan and confirm {metric_id} is "
                            f"below {threshold}, "
                            "with tests passing."
                        ),
                    },
                    location=location,
                    parents=(measurement.evidence_id,),
                )
                if finding is not None:
                    finding_count += 1

        for file_item in aggregate.files:
            measure_and_test(
                entity_kind="file",
                entity=file_item.path,
                language=file_item.language,
                path=file_item.path,
                line_start=None,
                line_end=None,
                metrics={
                    "physical_line_count": _metric_value(file_item.physical_line_count),
                    "type_count": _metric_value(file_item.type_count),
                    "callable_count": _metric_value(file_item.callable_count),
                },
                candidates=("large_file",),
            )
        for path in generic_paths:
            measure_and_test(
                entity_kind="file",
                entity=path,
                language=_LANGUAGE_SUFFIXES[Path(path).suffix.lower()].lower(),
                path=path,
                line_start=None,
                line_end=None,
                metrics={
                    "physical_line_count": len(texts[path].splitlines()),
                    "type_count": None,
                    "callable_count": None,
                },
                candidates=("large_file",),
            )
        for type_item in aggregate.types:
            measure_and_test(
                entity_kind="type",
                entity=type_item.qualified_name,
                language=type_item.language,
                path=type_item.path,
                line_start=type_item.span.line_start,
                line_end=type_item.span.line_end,
                metrics={
                    "physical_line_count": _metric_value(type_item.physical_line_count),
                    "callable_count": _metric_value(type_item.callable_count),
                },
                candidates=("large_type",),
            )
        for callable_item in aggregate.callables:
            measure_and_test(
                entity_kind="callable",
                entity=callable_item.qualified_signature,
                language=callable_item.language,
                path=callable_item.path,
                line_start=callable_item.span.line_start,
                line_end=callable_item.span.line_end,
                metrics={
                    "physical_line_count": _metric_value(callable_item.physical_line_count),
                    "parameter_count": _metric_value(callable_item.parameter_count),
                    "branch_point_count": _metric_value(callable_item.branch_point_count),
                    "max_nesting_depth": _metric_value(callable_item.max_nesting_depth),
                },
                candidates=("long_callable", "complex_callable", "deep_nesting", "parameter_bloat"),
            )
        if limit_reached:
            coverage = coverage.model_copy(
                update={
                    "state": CoverageState.PARTIAL,
                    "supports_absence_conclusion": False,
                    "limitations": (*coverage.limitations, "Evidence-record limit reached."),
                }
            )
            evidence = [item.model_copy(update={"coverage": coverage}) for item in evidence]
        summary = EvidenceEnvelope.create(
            kind="code-health.coverage",
            run_id=context.run_id,
            activity_id=context.activity.activity_id,
            collector_id=self.manifest.collector_id,
            collector_version=self.manifest.version,
            repository_id=context.plan.subject.repository_id,
            revision=context.plan.subject.revision,
            method="typed structural measurement with explicit user-selected thresholds",
            production_mode="observed",
            coverage=coverage,
            payload={
                "selected_biomarkers": selected,
                "thresholds": thresholds,
                "files_measured": len(aggregate.files) + len(generic_paths),
                "types_measured": len(aggregate.types),
                "callables_measured": len(aggregate.callables),
                "biomarker_findings": finding_count,
                "score_produced": False,
            },
        )
        evidence.insert(0, summary)
        return CollectionResult(
            evidence=tuple(evidence),
            coverage=coverage,
            diagnostics=tuple(aggregate.diagnostics),
        )


_REPOWISE_BIOMARKERS = (
    "brain_method",
    "low_cohesion",
    "god_class",
    "nested_complexity",
    "bumpy_road",
    "complex_conditional",
    "complex_method",
    "large_method",
    "primitive_obsession",
    "dry_violation",
    "untested_hotspot",
    "coverage_gap",
    "coverage_gradient",
    "developer_congestion",
    "knowledge_loss",
    "hidden_coupling",
    "function_hotspot",
    "code_age_volatility",
    "ownership_risk",
    "churn_risk",
    "change_entropy",
    "co_change_scatter",
    "prior_defect",
    "large_assertion_block",
    "duplicated_assertion_block",
    "error_handling",
)


class RepoWiseHealthCollector:
    """Optional process-boundary adapter; no RepoWise code is linked or copied."""

    manifest = CollectorManifest(
        collector_id="external.repowise-health",
        version="1.0.0",
        label="RepoWise code-health enrichment",
        description=(
            "Runs a separately installed RepoWise CLI in deterministic JSON mode and "
            "normalizes its measurements and selected biomarker findings."
        ),
        publisher="RepoWise / CodeStrata process adapter",
        output_kinds=(
            "code-health.provider-summary",
            "code-health.measurement",
            "code-health.biomarker",
        ),
        permission_requirements=("read_repository", "execute_local_tool"),
        cost_class=CostClass.HIGH,
        deterministic=True,
        runs_code=True,
        external_access=ExternalAccess.NONE,
        coverage_semantics="Files reported by the selected installed RepoWise version.",
        limitations=(
            "Requires a separately installed RepoWise executable; CodeStrata does "
            "not auto-install it.",
            "Scores and empirical claims belong to the installed RepoWise version, not CodeStrata.",
            "The JSON CLI currently reports file locations but not every internal line span.",
        ),
        configuration_schema={
            "type": "object",
            "properties": {
                "biomarkers": {
                    "type": "array",
                    "items": {"type": "string", "enum": list(_REPOWISE_BIOMARKERS)},
                    "default": list(_REPOWISE_BIOMARKERS),
                }
            },
        },
        license="AGPL-3.0 external executable or separate commercial license",
        homepage="https://github.com/repowise-dev/repowise",
        family=EvidenceFamily.CODE_HEALTH,
        capability_ids=tuple(f"biomarker.{item}" for item in _REPOWISE_BIOMARKERS),
        maturity=CollectorMaturity.PARTIAL,
        recommendation_weight=95,
    )

    def available(self) -> tuple[bool, str]:
        executable = shutil.which("repowise")
        if executable is None:
            return False, "RepoWise is not installed; CodeStrata will not auto-install it."
        return True, f"Discovered {executable}."

    def applicable(self, context: CollectorContext) -> tuple[bool, str]:
        if not context.repository.is_dir():
            return False, "Repository path is not a directory."
        return True, "Repository can be analyzed by the installed RepoWise executable."

    def collect(self, context: CollectorContext) -> CollectionResult:
        executable = shutil.which("repowise")
        if executable is None:
            raise RuntimeError("RepoWise executable is not available")
        selected_raw = context.activity.configuration.get("biomarkers", list(_REPOWISE_BIOMARKERS))
        if not isinstance(selected_raw, list):
            raise ValueError("RepoWise biomarkers must be an array")
        selected = set(str(item) for item in selected_raw)
        unknown = sorted(selected - set(_REPOWISE_BIOMARKERS))
        if unknown:
            raise ValueError(f"unknown RepoWise biomarkers: {', '.join(unknown)}")
        completed = subprocess.run(
            [
                executable,
                "health",
                str(context.repository),
                "--format",
                "json",
                "--no-workspace",
            ],
            cwd=context.repository,
            check=False,
            capture_output=True,
            text=True,
            timeout=context.plan.limits.activity_timeout_seconds,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"RepoWise failed with exit {completed.returncode}: {completed.stderr[-500:]}"
            )
        document = json.loads(completed.stdout)
        metrics = document.get("metrics", [])
        findings = [
            item
            for item in document.get("findings", [])
            if str(item.get("biomarker_type", "")) in selected
        ]
        if not isinstance(metrics, list) or not isinstance(findings, list):
            raise ValueError("RepoWise JSON output has an unsupported shape")
        coverage = Coverage(
            state=CoverageState.COMPLETE,
            population="Files measured by the installed RepoWise health analyzer.",
            planned=len(metrics),
            examined=len(metrics),
            successful=True,
            supports_absence_conclusion=True,
            limitations=("Producer file-selection policy is owned by RepoWise.",),
        )
        evidence: list[EvidenceEnvelope] = []
        summary = EvidenceEnvelope.create(
            kind="code-health.provider-summary",
            run_id=context.run_id,
            activity_id=context.activity.activity_id,
            collector_id=self.manifest.collector_id,
            collector_version=self.manifest.version,
            repository_id=context.plan.subject.repository_id,
            revision=context.plan.subject.revision,
            method="RepoWise CLI JSON process adapter",
            production_mode="imported",
            coverage=coverage,
            payload={
                "provider": "repowise",
                "kpis": document.get("kpis", {}),
                "selected_biomarkers": sorted(selected),
                "metric_count": len(metrics),
                "finding_count": len(findings),
            },
        )
        evidence.append(summary)
        measurement_ids: dict[str, str] = {}
        for item in metrics:
            if len(evidence) >= context.plan.limits.max_evidence_records:
                break
            path = str(item.get("file_path", "unknown"))
            measurement = EvidenceEnvelope.create(
                kind="code-health.measurement",
                run_id=context.run_id,
                activity_id=context.activity.activity_id,
                collector_id=self.manifest.collector_id,
                collector_version=self.manifest.version,
                repository_id=context.plan.subject.repository_id,
                revision=context.plan.subject.revision,
                method="RepoWise CLI JSON process adapter",
                production_mode="imported",
                coverage=coverage,
                payload={"entity_kind": "file", "entity": path, "metrics": item},
                locations=(EvidenceLocation(path=path),),
                parent_evidence_ids=(summary.evidence_id,),
            )
            evidence.append(measurement)
            measurement_ids[path] = measurement.evidence_id
        for item in findings:
            if len(evidence) >= context.plan.limits.max_evidence_records:
                break
            path = str(item.get("file_path", "unknown"))
            biomarker_id = str(item.get("biomarker_type", "unknown"))
            severity = str(item.get("severity", "unknown")).split(".")[-1].lower()
            reason = str(item.get("reason") or f"RepoWise reported {biomarker_id}.")
            evidence.append(
                EvidenceEnvelope.create(
                    kind="code-health.biomarker",
                    run_id=context.run_id,
                    activity_id=context.activity.activity_id,
                    collector_id=self.manifest.collector_id,
                    collector_version=self.manifest.version,
                    repository_id=context.plan.subject.repository_id,
                    revision=context.plan.subject.revision,
                    method="RepoWise CLI JSON process adapter",
                    production_mode="imported",
                    coverage=coverage,
                    payload={
                        "provider": "repowise",
                        "biomarker_id": biomarker_id,
                        "entity_kind": "file",
                        "entity": path,
                        "severity": severity,
                        "reason": reason,
                        "health_impact": item.get("health_impact"),
                        "details": item.get("details", {}),
                        "action_title": (
                            f"Address RepoWise {biomarker_id.replace('_', ' ')} finding"
                        ),
                        "action_rationale": reason,
                        "verification": (
                            "Re-run the same RepoWise-backed evidence plan and confirm the finding "
                            "is absent or explicitly accepted."
                        ),
                    },
                    locations=(EvidenceLocation(path=path),),
                    parent_evidence_ids=tuple(
                        item for item in (measurement_ids.get(path), summary.evidence_id) if item
                    ),
                )
            )
        return CollectionResult(
            evidence=tuple(evidence),
            coverage=coverage,
            raw_artifacts=(
                CollectedRawArtifact(
                    content=completed.stdout.encode("utf-8"),
                    media_type="application/json",
                ),
            ),
        )


class TrivyCollectorAdapter:
    manifest = CollectorManifest(
        collector_id="external.trivy",
        version="1.0.0",
        label="Trivy repository evidence",
        description=(
            "Optional user-installed Trivy adapter. Runs only when selected and "
            "external access is explicitly allowed by the plan."
        ),
        publisher="Aqua Security / CodeStrata adapter",
        output_kinds=("analysis.finding",),
        permission_requirements=("read_repository", "execute_local_tool"),
        cost_class=CostClass.HIGH,
        deterministic=False,
        runs_code=True,
        external_access=ExternalAccess.OPTIONAL,
        coverage_semantics="Coverage reported by Trivy for selected scanners.",
        limitations=(
            "Results depend on the installed Trivy version and vulnerability databases.",
            "Secret scanning is disabled unless explicitly selected.",
        ),
        configuration_schema={
            "type": "object",
            "properties": {
                "scanners": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["vuln", "misconfig", "secret", "license"],
                    },
                    "default": ["misconfig"],
                }
            },
        },
        license="Apache-2.0",
        homepage="https://github.com/aquasecurity/trivy",
        family=EvidenceFamily.SECURITY,
        capability_ids=(
            "security.vulnerabilities",
            "security.misconfiguration",
            "security.secrets",
            "dependencies.licenses",
        ),
        maturity=CollectorMaturity.PARTIAL,
    )

    def available(self) -> tuple[bool, str]:
        executable = shutil.which("trivy")
        if executable is None:
            return False, "Trivy is not installed; CodeStrata will not auto-install it."
        return True, f"Discovered {executable}."

    def applicable(self, context: CollectorContext) -> tuple[bool, str]:
        if context.plan.limits.external_access != "allow":
            return False, "Plan denies external access for database-backed tools."
        if context.plan.sensitivity.raw_artifacts != "copied":
            return False, "Trivy requires copied raw artifacts for reproducible provenance."
        return True, "Explicitly selected with external access allowed."

    def collect(self, context: CollectorContext) -> CollectionResult:
        from codestrata.application.evidence.framework.sarif import normalize_sarif_document

        scanners = context.activity.configuration.get("scanners", ["misconfig"])
        if not isinstance(scanners, list) or not scanners:
            raise ValueError("Trivy scanners must be a non-empty list")
        completed = subprocess.run(
            [
                "trivy",
                "fs",
                "--quiet",
                "--format",
                "sarif",
                "--scanners",
                ",".join(str(item) for item in scanners),
                ".",
            ],
            cwd=context.repository,
            check=False,
            capture_output=True,
            text=True,
            timeout=context.plan.limits.activity_timeout_seconds,
        )
        if completed.returncode not in {0, 1}:
            raise RuntimeError(
                f"Trivy failed with exit {completed.returncode}: {completed.stderr[-500:]}"
            )
        document = json.loads(completed.stdout)
        evidence, coverage = normalize_sarif_document(
            document=document,
            context=context,
            collector_id=self.manifest.collector_id,
            collector_version=self.manifest.version,
        )
        return CollectionResult(
            evidence=evidence,
            coverage=coverage,
            raw_artifacts=(
                CollectedRawArtifact(
                    content=completed.stdout.encode("utf-8"),
                    media_type="application/sarif+json",
                ),
            ),
        )


def create_default_registry() -> CollectorRegistry:
    language_registry = create_language_evidence_registry()
    language_collectors = tuple(
        LanguageProviderCollectorAdapter(language_registry.get(str(metadata.provider_id)))
        for metadata in language_registry.list_providers()
    )
    return CollectorRegistry(
        (
            RepositoryInventoryCollector(),
            FilePatternCollector(),
            DependencyCollectorAdapter(),
            TestingStructureCollectorAdapter(),
            StructuralHealthCollector(),
            RepoWiseHealthCollector(),
            TrivyCollectorAdapter(),
            *language_collectors,
        )
    )
