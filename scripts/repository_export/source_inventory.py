"""Source inventory walk for Infrastructure export."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from repository_export.errors import (
    ProhibitedSourceFile,
    SourceFileUnclassified,
    SourceLayoutInvalid,
    SymlinkNotAllowed,
)
from repository_export.path_rules import approach_a_map, ensure_unique_mappings, to_posix
from repository_export.policy import REQUIRED_SOURCE_FILES, REQUIRED_SOURCE_PREFIXES
from repository_export.prohibited_files import (
    content_looks_like_secret_blob,
    excluded_category_for,
    is_fail_closed_name,
    is_provider_lock,
    is_real_tfvars,
    path_has_excluded_dir,
)
from repository_export.transform import transform_file


@dataclass
class SourceInventoryResult:
    mapped: dict[str, Path] = field(default_factory=dict)  # dest -> source path
    source_rel: dict[str, str] = field(default_factory=dict)  # dest -> monorepo rel
    excluded_categories: dict[str, int] = field(default_factory=dict)
    omitted: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


def _under_allowlist(rel: str) -> bool:
    if rel in REQUIRED_SOURCE_FILES:
        return True
    if rel == "infrastructure/.gitignore":
        return True  # consumed for generation, not mapped 1:1
    if rel == "infrastructure/__init__.py":
        return True  # intentionally omitted at destination
    for prefix in REQUIRED_SOURCE_PREFIXES:
        if rel.startswith(prefix):
            return True
    # Provider locks under allowlisted trees
    if rel.startswith("infrastructure/") and PurePosixPath(rel).name == ".terraform.lock.hcl":
        # only if parent path is under allowlisted prefix
        parent = str(PurePosixPath(rel).parent) + "/"
        for prefix in REQUIRED_SOURCE_PREFIXES:
            if parent.startswith(prefix) or rel.startswith(prefix):
                return True
    return False


def collect_source_inventory(source_root: Path) -> SourceInventoryResult:
    infra = source_root / "infrastructure"
    if not infra.is_dir():
        raise SourceLayoutInvalid("infrastructure/ missing")
    contract = infra / "docs" / "repository-contract.md"
    if not contract.is_file():
        raise SourceLayoutInvalid("repository-contract.md missing")

    result = SourceInventoryResult()
    lock_found = False

    for dirpath, dirnames, filenames in os.walk(infra, topdown=True, followlinks=False):
        # Prune excluded dirs early
        pruned: list[str] = []
        for name in list(dirnames):
            child = Path(dirpath) / name
            if child.is_symlink():
                raise SymlinkNotAllowed("symlink directory not allowed")
            rel_dir = to_posix(str(child.relative_to(source_root)))
            cat = excluded_category_for(rel_dir + "/")
            if name.startswith(".") and name in {".terraform", ".tofu", ".git"}:
                result.excluded_categories[cat or "provider_plugin_cache"] = (
                    result.excluded_categories.get(cat or "provider_plugin_cache", 0) + 1
                )
                pruned.append(name)
                continue
            if name in {
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "node_modules",
                "reports",
                ".venv",
                "venv",
            }:
                result.excluded_categories[cat or "generated_caches"] = (
                    result.excluded_categories.get(cat or "generated_caches", 0) + 1
                )
                pruned.append(name)
                continue
        dirnames[:] = sorted(n for n in dirnames if n not in pruned)

        for name in sorted(filenames):
            path = Path(dirpath) / name
            rel = to_posix(str(path.relative_to(source_root)))

            if path.is_symlink():
                raise SymlinkNotAllowed(f"symlink not allowed: {PurePosixPath(rel).name}")

            if path_has_excluded_dir(rel):
                cat = excluded_category_for(rel) or "generated_caches"
                result.excluded_categories[cat] = result.excluded_categories.get(cat, 0) + 1
                continue

            if is_real_tfvars(name) or is_fail_closed_name(name):
                raise ProhibitedSourceFile(
                    f"prohibited source file under infrastructure: {PurePosixPath(rel).name}"
                )

            if not _under_allowlist(rel):
                # Unexpected file at infrastructure root or elsewhere
                raise SourceFileUnclassified(
                    f"unclassified source file: {PurePosixPath(rel).as_posix()}"
                )

            if is_provider_lock(name):
                lock_found = True

            dest = approach_a_map(rel)
            if dest is None:
                result.omitted.append(rel)
                if rel.endswith("__init__.py"):
                    result.limitations.append("root_package_marker_omitted_approach_a")
                if rel.endswith(".gitignore"):
                    result.limitations.append("source_gitignore_replaced_by_generated")
                continue

            # Content safety
            data = path.read_bytes()
            if content_looks_like_secret_blob(data):
                raise ProhibitedSourceFile("secret-shaped content rejected")

            if dest in result.mapped:
                raise SourceFileUnclassified(f"duplicate destination mapping: {dest}")
            result.mapped[dest] = path
            result.source_rel[dest] = rel

    ensure_unique_mappings(result.source_rel)

    # Required prefixes must yield at least one file each
    for prefix in REQUIRED_SOURCE_PREFIXES:
        local = prefix.removeprefix("infrastructure/")
        if not any(s.startswith(prefix) for s in result.source_rel.values()) and not any(
            d.startswith(local.rstrip("/")) for d in result.mapped
        ):
            # modules etc. must exist
            if not (infra / local.rstrip("/")).exists():
                raise SourceLayoutInvalid(f"missing required tree: {prefix}")

    for required in REQUIRED_SOURCE_FILES:
        if required not in result.source_rel.values() and approach_a_map(required) not in result.mapped:
            # README must be present
            if not (source_root / required).is_file():
                raise SourceLayoutInvalid(f"missing required file: {required}")

    if not lock_found:
        result.limitations.append("provider_lock_files_absent")

    return result


def materialize_source_files(
    inventory: SourceInventoryResult,
) -> list:
    from repository_export.models import PlannedFile
    from repository_export.permissions import approved_mode_for

    planned: list[PlannedFile] = []
    for dest in sorted(inventory.mapped):
        path = inventory.mapped[dest]
        raw = path.read_bytes()
        content, classification = transform_file(dest, raw)
        # Optional examples keep export_optional
        src_rel = inventory.source_rel[dest]
        if src_rel.endswith(".example"):
            classification = "export_optional"
        mode = approved_mode_for(dest)
        planned.append(
            PlannedFile(
                destination_path=dest,
                content=content,
                mode=mode,
                classification=classification,  # type: ignore[arg-type]
                source_relative=src_rel,
            )
        )
    return planned
