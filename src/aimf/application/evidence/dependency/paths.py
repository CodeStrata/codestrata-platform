"""Manifest path selection for Dependency Evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath

from aimf.application.evidence.language.adapters import classify_source_path
from aimf.domain.evidence.dependency.enums import (
    DependencyEcosystem,
    DependencyManifestType,
)
from aimf.domain.evidence.language.capabilities import SourceClassification

DEFAULT_DEPENDENCY_IGNORE_MARKERS: tuple[str, ...] = (
    "/generated/",
    "/.generated/",
    "/vendor/",
    "/.aimf/",
    "/node_modules/",
    "/.git/",
    "/target/",
    "/dist/",
    "/build/",
    "/.venv/",
    "/venv/",
    "/__pycache__/",
)

_MANIFEST_BASENAMES: dict[str, tuple[DependencyEcosystem, DependencyManifestType]] = {
    "pom.xml": (DependencyEcosystem.MAVEN, DependencyManifestType.POM_XML),
    "build.gradle": (DependencyEcosystem.GRADLE, DependencyManifestType.BUILD_GRADLE),
    "build.gradle.kts": (
        DependencyEcosystem.GRADLE,
        DependencyManifestType.BUILD_GRADLE_KTS,
    ),
    "pyproject.toml": (
        DependencyEcosystem.PYTHON,
        DependencyManifestType.PYPROJECT_TOML,
    ),
}


def normalize_relative_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def is_ignored_path(
    path: str,
    *,
    ignore_markers: Sequence[str] = DEFAULT_DEPENDENCY_IGNORE_MARKERS,
) -> bool:
    lower = normalize_relative_path(path).lower()
    if lower.startswith(".aimf/") or "/.aimf/" in lower:
        return True
    for marker in ignore_markers:
        compact = marker.strip().lower()
        if not compact:
            continue
        if compact in lower:
            return True
        stripped = compact.lstrip("/")
        if stripped and (lower.startswith(stripped) or f"/{stripped}" in lower):
            return True
    return False


def classify_manifest_basename(
    path: str,
) -> tuple[DependencyEcosystem, DependencyManifestType] | None:
    name = PurePosixPath(normalize_relative_path(path)).name.lower()
    if name in _MANIFEST_BASENAMES:
        return _MANIFEST_BASENAMES[name]
    # requirements*.txt family
    if name == "requirements.txt" or (
        name.startswith("requirements") and name.endswith(".txt")
    ):
        return DependencyEcosystem.PYTHON, DependencyManifestType.REQUIREMENTS_TXT
    return None


def select_manifest_paths(
    relative_paths: Sequence[str],
    *,
    ignore_markers: Sequence[str] = DEFAULT_DEPENDENCY_IGNORE_MARKERS,
    max_files: int = 500,
    ecosystems: Sequence[DependencyEcosystem] | None = None,
) -> tuple[tuple[str, ...], int]:
    """Return (sorted eligible manifest paths, excluded_count)."""

    allowed = set(ecosystems) if ecosystems is not None else None
    eligible: list[str] = []
    excluded = 0
    for raw in relative_paths:
        path = normalize_relative_path(raw)
        if not path:
            continue
        classified = classify_manifest_basename(path)
        if classified is None:
            continue
        ecosystem, _manifest_type = classified
        if allowed is not None and ecosystem not in allowed:
            continue
        if is_ignored_path(path, ignore_markers=ignore_markers):
            excluded += 1
            continue
        eligible.append(path)
    ordered = tuple(sorted(set(eligible)))
    if len(ordered) > max_files:
        return ordered[:max_files], excluded + (len(ordered) - max_files)
    return ordered, excluded


def texts_for_paths(
    paths: Sequence[str],
    file_texts: Mapping[str, str],
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in paths:
        if path in file_texts:
            mapping[path] = file_texts[path]
            continue
        alt = path.replace("/", "\\")
        if alt in file_texts:
            mapping[path] = file_texts[alt]
    return mapping


def classification_for_path(path: str) -> SourceClassification:
    return classify_source_path(path)
