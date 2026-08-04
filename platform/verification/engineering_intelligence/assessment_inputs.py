"""Prepare canonical Engine assessments for SV.6 via SV.4 workflow helpers."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from verification.engineering_intelligence.catalog import (
    CatalogRepository,
    PermanentCatalog,
    load_permanent_catalog,
    monorepo_root_from_here,
    resolve_subset,
)
from verification.engineering_intelligence.contract import ASSESSMENT_SCHEMA_VERSION


def _ensure_engine_verification_path(monorepo: Path) -> None:
    """Append Engine root so SV.4 helpers resolve via verification namespace merge."""

    engine = str((monorepo / "engine").resolve())
    if engine not in sys.path:
        sys.path.append(engine)
    import verification as verification_pkg
    from pkgutil import extend_path

    verification_pkg.__path__ = extend_path(
        list(verification_pkg.__path__), verification_pkg.__name__
    )


@dataclass(frozen=True, slots=True)
class PreparedAssessment:
    repository_id: str
    project_name: str
    github_repository: str
    qualified_revision: str
    source_tag: str | None
    language_group: str
    assessment_run_reference: str
    report_path: Path
    report_digest: str
    schema_version: str
    source: str
    report_document: dict[str, Any]


def _engine_root(monorepo: Path) -> Path:
    return monorepo / "engine"


def _stable_digest(document: dict[str, Any]) -> str:
    payload = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_report(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"report.json must be an object: {path.name}")
    schema = str(data.get("schema_version") or "")
    if schema != ASSESSMENT_SCHEMA_VERSION:
        raise ValueError(f"expected schema {ASSESSMENT_SCHEMA_VERSION}, got {schema}")
    return data


def _cache_dir_for(work_root: Path, repository_id: str, sha: str) -> Path:
    return work_root / "assessments" / repository_id / sha[:12]


def _try_load_cached(
    entry: CatalogRepository,
    work_root: Path,
) -> PreparedAssessment | None:
    sha = entry.qualified_revision.value
    dest = _cache_dir_for(work_root, entry.repository_id, sha)
    report_path = dest / "report.json"
    if not report_path.is_file():
        return None
    document = _load_report(report_path)
    return PreparedAssessment(
        repository_id=entry.repository_id,
        project_name=entry.project_name,
        github_repository=entry.github_repository,
        qualified_revision=sha,
        source_tag=entry.qualified_revision.source_tag,
        language_group=entry.language_group,
        assessment_run_reference=f"assessments/{entry.repository_id}/{sha[:12]}",
        report_path=report_path,
        report_digest=_stable_digest(document),
        schema_version=str(document.get("schema_version") or ""),
        source="cache",
        report_document=document,
    )


def _install_codestrata(engine_root: Path, venv_dir: Path, env: dict[str, str]) -> Path:
    import subprocess

    from verification.cli_installation.environment import venv_codestrata, venv_python

    venv.create(str(venv_dir), with_pip=True, clear=True)
    python = venv_python(venv_dir)
    proc = subprocess.run(
        [str(python), "-m", "pip", "install", str(engine_root)],
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"engine install failed: {(proc.stderr or '')[-400:]}")
    return venv_codestrata(venv_dir)


def _assess_catalog_entry(
    *,
    entry: CatalogRepository,
    codestrata: Path,
    scratch: Path,
    work_root: Path,
    monorepo: Path,
    env: dict[str, str],
) -> PreparedAssessment:
    _ensure_engine_verification_path(monorepo)
    from verification.repository_assessment.clone import clone_qualified_repository
    from verification.repository_assessment.commands import (
        assessment_environ,
        run_assess,
        run_doctor,
        run_init,
    )
    from verification.repository_assessment.artifacts import find_latest_run_directory
    from verification.repository_assessment.workspace import assert_outside_codestrata_tree

    # Adapt CatalogRepository → engine CatalogEntry shape.
    from verification.repository_assessment.catalog import (
        CatalogEntry,
        QualifiedRevision as EngineQualifiedRevision,
    )

    engine_entry = CatalogEntry(
        id=entry.repository_id,
        project_name=entry.project_name,
        github_repository=entry.github_repository,
        github_url=entry.github_url,
        language_group=entry.language_group,
        candidate_category=entry.candidate_category,
        license=entry.license,
        qualified_revision=EngineQualifiedRevision(
            entry.qualified_revision.revision_type,
            entry.qualified_revision.value,
            entry.qualified_revision.source_tag,
        ),
        enabled_for_smoke=True,
        selection_reason="sv6_preferred_subset",
    )
    clone_dest = scratch / "clones" / entry.repository_id
    assert_outside_codestrata_tree(clone_dest, monorepo)
    clone = clone_qualified_repository(engine_entry, clone_dest)
    if not clone.ok:
        raise RuntimeError(f"clone failed for {entry.repository_id}: {clone.detail}")
    if (clone.checked_out_sha or "").lower() != entry.qualified_revision.value.lower():
        raise RuntimeError(
            f"SHA mismatch for {entry.repository_id}: "
            f"expected {entry.qualified_revision.value} got {clone.checked_out_sha}"
        )

    offline = assessment_environ(env, offline=True)
    run_doctor(codestrata, cwd=clone_dest, env=offline)
    init = run_init(codestrata, cwd=clone_dest, env=offline)
    if init.exit_code != 0:
        raise RuntimeError(f"init failed for {entry.repository_id}: {init.exit_code}")
    assess = run_assess(codestrata, cwd=clone_dest, env=offline)
    if assess.exit_code != 0:
        raise RuntimeError(f"assess failed for {entry.repository_id}: {assess.exit_code}")
    run_dir = find_latest_run_directory(clone_dest / "reports")
    if run_dir is None or not (run_dir / "report.json").is_file():
        raise RuntimeError(f"assessment artifacts missing for {entry.repository_id}")

    sha = entry.qualified_revision.value
    dest = _cache_dir_for(work_root, entry.repository_id, sha)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    # Copy only report.json for EI ingestion (bounded; no HTML/source).
    shutil.copy2(run_dir / "report.json", dest / "report.json")
    meta = {
        "repository_id": entry.repository_id,
        "github_repository": entry.github_repository,
        "qualified_revision": sha,
        "source_tag": entry.qualified_revision.source_tag,
        "language_group": entry.language_group,
        "assessment_command": "codestrata assess --repo . --output reports --no-ai",
    }
    (dest / "assessment-meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    document = _load_report(dest / "report.json")
    return PreparedAssessment(
        repository_id=entry.repository_id,
        project_name=entry.project_name,
        github_repository=entry.github_repository,
        qualified_revision=sha,
        source_tag=entry.qualified_revision.source_tag,
        language_group=entry.language_group,
        assessment_run_reference=f"assessments/{entry.repository_id}/{sha[:12]}",
        report_path=dest / "report.json",
        report_digest=_stable_digest(document),
        schema_version=str(document.get("schema_version") or ""),
        source="catalog_assess",
        report_document=document,
    )


def prepare_catalog_assessments(
    *,
    monorepo: Path | None = None,
    work_root: Path | None = None,
    repository_ids: tuple[str, ...] | None = None,
    with_catalog_network: bool = False,
    reuse_cache: bool = True,
) -> tuple[list[PreparedAssessment], PermanentCatalog, Path]:
    """Resolve catalog subset and return schema-1.2 assessments.

    When ``with_catalog_network`` is false, only cached verified assessments are
    used (unit/integration without clone). Network mode clones pinned SHAs and
    runs the canonical offline assess workflow.
    """

    monorepo = (monorepo or monorepo_root_from_here()).resolve()
    catalog = load_permanent_catalog(monorepo)
    entries = resolve_subset(catalog, repository_ids=repository_ids)

    owned = work_root is None
    artifact_root = (work_root or Path(tempfile.mkdtemp(prefix="cs-sv6-artifacts-"))).resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)

    prepared: list[PreparedAssessment] = []
    missing_cache: list[CatalogRepository] = []
    for entry in entries:
        if reuse_cache:
            cached = _try_load_cached(entry, artifact_root)
            if cached is not None:
                prepared.append(cached)
                continue
        missing_cache.append(entry)

    if not missing_cache:
        return prepared, catalog, artifact_root

    if not with_catalog_network:
        ids = ", ".join(e.repository_id for e in missing_cache)
        raise FileNotFoundError(
            "cached assessments missing for: "
            f"{ids}. Re-run with --with-catalog-network or provide --cache-dir."
        )

    # Generate missing assessments via SV.4-style workflow.
    _ensure_engine_verification_path(monorepo)
    from verification.cli_installation.environment import (
        scrub_environ,
        with_venv_path,
    )
    from verification.repository_assessment.workspace import assert_outside_codestrata_tree

    scratch = Path(tempfile.mkdtemp(prefix="cs-sv6-scratch-")).resolve()
    assert_outside_codestrata_tree(scratch, monorepo)
    try:
        base_env = scrub_environ()
        venv_dir = scratch / "venv"
        install_env = with_venv_path(base_env, venv_dir)
        codestrata = _install_codestrata(_engine_root(monorepo), venv_dir, install_env)
        run_env = with_venv_path(base_env, venv_dir)
        for entry in missing_cache:
            prepared.append(
                _assess_catalog_entry(
                    entry=entry,
                    codestrata=codestrata,
                    scratch=scratch,
                    work_root=artifact_root,
                    monorepo=monorepo,
                    env=run_env,
                )
            )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    # Preserve deterministic subset order.
    by_id = {item.repository_id: item for item in prepared}
    ordered = [by_id[e.repository_id] for e in entries]
    if owned:
        pass  # caller owns cleanup of tempfile if desired
    return ordered, catalog, artifact_root
