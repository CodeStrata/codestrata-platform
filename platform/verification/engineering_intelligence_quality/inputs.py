"""Load SV.10 assessments + SV.11 gate for SV.12 (no clone/reassess)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from verification.engineering_intelligence.assessment_inputs import PreparedAssessment
from verification.engineering_intelligence.catalog import (
    CatalogRepository,
    load_permanent_catalog,
    monorepo_root_from_here,
    resolve_subset,
)
from verification.engineering_intelligence.contract import ASSESSMENT_SCHEMA_VERSION
from verification.engineering_intelligence_quality.contract import (
    SV10_OUTPUT_RELATIVE,
    SV11_REPORT_RELATIVE,
    TARGET_REPOSITORY_COUNT,
)


class Sv12InputError(RuntimeError):
    """Raised when SV.10/SV.11 inputs are incomplete."""


@dataclass(frozen=True, slots=True)
class PermanentCatalogMeta:
    catalog_id: str
    catalog_schema_version: str
    entries: tuple[CatalogRepository, ...]


def _digest(document: dict[str, Any]) -> str:
    blob = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def resolve_sv10_dir(monorepo: Path | None = None) -> Path:
    root = (monorepo or monorepo_root_from_here()).resolve()
    path = root / SV10_OUTPUT_RELATIVE
    if not path.is_dir():
        raise Sv12InputError(f"missing SV.10 output directory: {SV10_OUTPUT_RELATIVE}")
    return path


def load_sv11_gate(monorepo: Path | None = None) -> dict[str, Any]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    path = root / SV11_REPORT_RELATIVE
    if not path.is_file():
        raise Sv12InputError(f"missing SV.11 report: {SV11_REPORT_RELATIVE}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("repository_count") != TARGET_REPOSITORY_COUNT:
        raise Sv12InputError(
            f"SV.11 repository_count={data.get('repository_count')} != {TARGET_REPOSITORY_COUNT}"
        )
    ready = data.get("engineering_intelligence_input_ready") or {}
    ids = data.get("included_repository_ids") or []
    if not isinstance(ready, dict) or not all(ready.get(rid) for rid in ids):
        raise Sv12InputError("SV.11 engineering_intelligence_input_ready incomplete")
    if data.get("verdict") not in {"PASS", "PASS_WITH_LIMITATIONS"}:
        raise Sv12InputError(f"SV.11 verdict blocks SV.12: {data.get('verdict')}")
    return data


def release_validation_ids(monorepo: Path | None = None) -> tuple[str, ...]:
    """Resolve the 22 release_validation IDs from catalog metadata."""

    root = (monorepo or monorepo_root_from_here()).resolve()
    catalog_path = root / "validation" / "repository-catalog" / "catalog.json"
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    ids: list[str] = []
    for item in data.get("repositories") or []:
        if not isinstance(item, dict):
            continue
        enabled = item.get("enabled_for") or {}
        if enabled.get("release_validation"):
            rid = str(item.get("id") or "")
            if rid:
                ids.append(rid)
    if len(ids) != TARGET_REPOSITORY_COUNT:
        raise Sv12InputError(
            f"catalog release_validation count {len(ids)} != {TARGET_REPOSITORY_COUNT}"
        )
    return tuple(sorted(ids))


def _artifact_report_path(sv10: Path, repository_id: str, sha: str) -> Path:
    preferred = sv10 / "artifacts" / repository_id / sha[:12] / "report.json"
    if preferred.is_file():
        return preferred
    base = sv10 / "artifacts" / repository_id
    if not base.is_dir():
        raise Sv12InputError(f"missing SV.10 artifacts for {repository_id}")
    matches = sorted(base.glob("*/report.json"))
    if len(matches) == 1:
        return matches[0]
    raise Sv12InputError(f"ambiguous/missing report.json for {repository_id}")


def load_prepared_assessments_from_sv10(
    *,
    monorepo: Path | None = None,
    repository_ids: tuple[str, ...] | None = None,
) -> tuple[list[PreparedAssessment], dict[str, Any], PermanentCatalogMeta]:
    root = (monorepo or monorepo_root_from_here()).resolve()
    sv10 = resolve_sv10_dir(root)
    sv11 = load_sv11_gate(root)
    catalog = load_permanent_catalog(root)
    wanted = repository_ids or release_validation_ids(root)
    entries = resolve_subset(catalog, repository_ids=wanted)
    if len(entries) != TARGET_REPOSITORY_COUNT:
        raise Sv12InputError(
            f"resolved {len(entries)} repositories, expected {TARGET_REPOSITORY_COUNT}"
        )

    assessments: list[PreparedAssessment] = []
    for entry in entries:
        record_path = sv10 / "records" / f"{entry.repository_id}.json"
        if not record_path.is_file():
            raise Sv12InputError(f"missing SV.10 record for {entry.repository_id}")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        sha = str(record.get("final_checkout_sha") or entry.qualified_revision.value)
        if sha != entry.qualified_revision.value:
            raise Sv12InputError(
                f"{entry.repository_id}: record SHA mismatch "
                f"catalog={entry.qualified_revision.value} record={sha}"
            )
        report_path = _artifact_report_path(sv10, entry.repository_id, sha)
        document = json.loads(report_path.read_text(encoding="utf-8"))
        if str(document.get("schema_version")) != ASSESSMENT_SCHEMA_VERSION:
            raise Sv12InputError(
                f"{entry.repository_id}: schema {document.get('schema_version')} "
                f"!= {ASSESSMENT_SCHEMA_VERSION}"
            )
        # Apply the Engine customer-safe projection before Platform EI ingestion.
        # Preserves entity IDs; rewrites secret-shaped presentation text only.
        from codestrata.security.customer_safe_text import (
            ensure_customer_safe_report_document,
        )

        document = ensure_customer_safe_report_document(document)
        assessments.append(
            PreparedAssessment(
                repository_id=entry.repository_id,
                project_name=entry.project_name,
                github_repository=entry.github_repository,
                qualified_revision=sha,
                source_tag=entry.qualified_revision.source_tag,
                language_group=entry.language_group,
                assessment_run_reference=(
                    f"sv10/artifacts/{entry.repository_id}/{sha[:12]}"
                ),
                report_path=report_path,
                report_digest=_digest(document),
                schema_version=ASSESSMENT_SCHEMA_VERSION,
                source="sv10_preserved",
                report_document=document,
            )
        )
    meta = PermanentCatalogMeta(
        catalog_id=catalog.catalog_id,
        catalog_schema_version=catalog.schema_version,
        entries=entries,
    )
    return assessments, sv11, meta
