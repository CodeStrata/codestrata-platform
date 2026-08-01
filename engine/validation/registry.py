"""Load validation repository definitions and expectations."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from validation.models import ExpectedResults, ValidationRepository
from validation.paths import REPOSITORIES_DIR, VALIDATION_ROOT, resolve_local_path


class RegistryError(ValueError):
    """Invalid repository registry content."""


def load_repository_definition(path: Path) -> ValidationRepository:
    payload = _load_mapping(path)
    return ValidationRepository.model_validate(payload)


def load_expected_results(path: Path) -> ExpectedResults:
    payload = _load_mapping(path)
    return ExpectedResults.model_validate(payload)


def load_all_repositories(
    *,
    repositories_dir: Path = REPOSITORIES_DIR,
) -> tuple[ValidationRepository, ...]:
    if not repositories_dir.is_dir():
        return ()
    definitions: list[ValidationRepository] = []
    seen: set[str] = set()
    for path in sorted(repositories_dir.glob("*")):
        if path.suffix.lower() not in {".toml", ".json"}:
            continue
        if path.name.startswith("."):
            continue
        definition = load_repository_definition(path)
        if definition.repository_id in seen:
            raise RegistryError(f"duplicate repository_id: {definition.repository_id}")
        seen.add(definition.repository_id)
        definitions.append(definition)
    return tuple(definitions)


def resolve_expected_results(
    definition: ValidationRepository,
    *,
    validation_root: Path = VALIDATION_ROOT,
) -> ExpectedResults:
    path = validation_root / definition.expected_results_path
    if not path.is_file():
        raise RegistryError(
            f"expected results not found for {definition.repository_id}: {path}"
        )
    return load_expected_results(path)


def resolve_repository_workdir(
    definition: ValidationRepository,
    *,
    validation_root: Path = VALIDATION_ROOT,
) -> Path:
    if definition.local_path is None:
        raise RegistryError(f"{definition.repository_id} has no local_path")
    path = resolve_local_path(definition.local_path, validation_root=validation_root)
    if not path.is_dir():
        raise RegistryError(
            f"local repository path does not exist for {definition.repository_id}: "
            f"{definition.local_path}"
        )
    return path


def filter_repositories(
    definitions: tuple[ValidationRepository, ...],
    *,
    repository_ids: set[str] | None = None,
    tags: set[str] | None = None,
    local_only: bool = False,
    include_remote: bool = False,
    include_disabled: bool = False,
) -> tuple[ValidationRepository, ...]:
    selected: list[ValidationRepository] = []
    for definition in definitions:
        if not include_disabled and not definition.enabled:
            continue
        if repository_ids is not None and definition.repository_id not in repository_ids:
            continue
        if tags is not None and not (set(definition.tags) & tags):
            continue
        if definition.source_type.value == "remote":
            if local_only or not include_remote:
                continue
        selected.append(definition)
    if repository_ids is not None:
        missing = repository_ids - {item.repository_id for item in selected}
        # Remotes filtered by mode are not "missing" — runner marks SKIPPED.
        known = {item.repository_id for item in definitions}
        unknown = repository_ids - known
        if unknown:
            raise RegistryError(f"unknown repository id(s): {sorted(unknown)}")
        _ = missing
    return tuple(selected)


def _load_mapping(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".toml":
        payload = tomllib.loads(text)
    elif path.suffix.lower() == ".json":
        payload = json.loads(text)
    else:
        raise RegistryError(f"unsupported definition format: {path}")
    if not isinstance(payload, dict):
        raise RegistryError(f"definition must be a mapping: {path}")
    return payload
