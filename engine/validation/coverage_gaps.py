"""Coverage-gap derivation for Slice 4.12 validation summaries.

Gaps are factual engineering notes derived from records, the validation matrix,
and a small explicit registry for structural gaps that records cannot express.
They are never converted into failures unless an expectation was violated.
"""

from __future__ import annotations

from validation.matrix import ACTIVE_VALIDATION_SET, VALIDATION_MATRIX
from validation.recording import RepositoryValidationRecord
from validation.summary_artifact import CANONICAL_PACKS, CoverageGap, PackAggregateSummary

# Explicit gaps that cannot be fully derived from current structured records alone.
# Keep this list small and documented.
_EXPLICIT_GAP_REGISTRY: tuple[CoverageGap, ...] = (
    CoverageGap(
        gap_id="gap.languages.beyond-active-set",
        category="repository_coverage",
        description=(
            "Active validation set covers Java, Python, JavaScript, TypeScript, C#, and PHP; "
            "additional languages/frameworks beyond detector support remain out of scope."
        ),
        related_packs=(),
        related_repositories=ACTIVE_VALIDATION_SET,
        derived_from="registry",
    ),
    CoverageGap(
        gap_id="gap.dependency.npm-hygiene-unsupported",
        category="pack_capability",
        description=(
            "npm dependency hygiene positive controls remain limited in the active set; "
            "absence of TP for specific hygiene families is a coverage gap, not a pack failure."
        ),
        related_packs=("dependency",),
        related_repositories=("local-sample-js",),
        derived_from="registry",
    ),
    CoverageGap(
        gap_id="gap.cloud.compose-managed-service",
        category="pack_capability",
        description=(
            "Compose postgres/redis image names are not modeled as managed_service signals; "
            "managed_service patterns remain IaC-oriented (coverage gap, not a failure)."
        ),
        related_packs=("cloud",),
        related_repositories=("local-compose-managed",),
        derived_from="registry",
    ),
)


def derive_coverage_gaps(
    *,
    records: tuple[RepositoryValidationRecord, ...],
    pack_summaries: tuple[PackAggregateSummary, ...],
) -> tuple[CoverageGap, ...]:
    """Build a deterministic coverage-gap list from records + matrix + registry."""

    gaps: list[CoverageGap] = []
    seen: set[str] = set()

    def _add(gap: CoverageGap) -> None:
        if gap.gap_id in seen:
            return
        seen.add(gap.gap_id)
        gaps.append(gap)

    pack_by_name = {item.pack: item for item in pack_summaries}
    for pack in CANONICAL_PACKS:
        summary = pack_by_name.get(pack)
        if summary is None:
            _add(
                CoverageGap(
                    gap_id=f"gap.pack.{pack}.absent",
                    category="unavailable_metrics",
                    description=f"No pack precision records present for pack '{pack}'.",
                    related_packs=(pack,),
                    related_repositories=(),
                    derived_from="records",
                )
            )
            continue
        if summary.repositories_evaluated == 0:
            _add(
                CoverageGap(
                    gap_id=f"gap.pack.{pack}.unevaluated",
                    category="unavailable_metrics",
                    description=f"Pack '{pack}' was not evaluated on any selected repository.",
                    related_packs=(pack,),
                    related_repositories=(),
                    derived_from="records",
                )
            )
            continue
        if summary.true_positives == 0:
            _add(
                CoverageGap(
                    gap_id=f"gap.pack.{pack}.zero-tp",
                    category="zero_true_positives",
                    description=(
                        f"Pack '{pack}' has aggregate true_positives=0 across evaluated "
                        "repositories (coverage gap, not an automatic failure)."
                    ),
                    related_packs=(pack,),
                    related_repositories=summary.source_repository_ids,
                    derived_from="records",
                )
            )
        if summary.precision is None:
            _add(
                CoverageGap(
                    gap_id=f"gap.pack.{pack}.precision-unavailable",
                    category="unavailable_metrics",
                    description=(
                        f"Aggregate precision for pack '{pack}' is unavailable "
                        "(TP+FP=0); metric is not treated as 0 or 1."
                    ),
                    related_packs=(pack,),
                    related_repositories=summary.source_repository_ids,
                    derived_from="records",
                )
            )
        if summary.recall is None:
            _add(
                CoverageGap(
                    gap_id=f"gap.pack.{pack}.recall-unavailable",
                    category="unavailable_metrics",
                    description=(
                        f"Aggregate recall for pack '{pack}' is unavailable "
                        "(TP+FN=0); metric is not treated as 0 or 1."
                    ),
                    related_packs=(pack,),
                    related_repositories=summary.source_repository_ids,
                    derived_from="records",
                )
            )
        if summary.repositories_unavailable:
            _add(
                CoverageGap(
                    gap_id=f"gap.pack.{pack}.repo-unavailable",
                    category="unavailable_metrics",
                    description=(
                        f"Pack '{pack}' has {summary.repositories_unavailable} "
                        "repository(ies) with unavailable pack precision."
                    ),
                    related_packs=(pack,),
                    related_repositories=summary.source_repository_ids,
                    derived_from="records",
                )
            )

    # Matrix-derived: intentional "none" signals on active repos that still ran packs.
    matrix_pack_map = {
        "security_signal": "security",
        "cloud_signal": "cloud",
        "ai_readiness_signal": "ai_readiness",
    }
    for repository_id in sorted({item.repository_id for item in records}):
        row = VALIDATION_MATRIX.get(repository_id)
        if not row:
            continue
        for signal_key, pack in matrix_pack_map.items():
            signal = row.get(signal_key, "")
            if "none intentional" not in signal.lower():
                continue
            summary = pack_by_name.get(pack)
            if summary and summary.true_positives == 0 and repository_id in summary.source_repository_ids:
                _add(
                    CoverageGap(
                        gap_id=f"gap.matrix.{repository_id}.{pack}.negative-control",
                        category="negative_control",
                        description=(
                            f"Matrix marks {signal_key} as '{signal}' for {repository_id}; "
                            f"pack '{pack}' contributes no positive TP on this control."
                        ),
                        related_packs=(pack,),
                        related_repositories=(repository_id,),
                        derived_from="matrix",
                    )
                )

    for gap in _EXPLICIT_GAP_REGISTRY:
        _add(gap)

    return tuple(sorted(gaps, key=lambda item: (item.category, item.gap_id)))
