"""Fail-closed validation for report confidence and dataset limitations."""

from __future__ import annotations

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.report_quality.diagnostics import (
    ReportQualityDiagnostics,
)
from codestrata_platform.intelligence_reporting.application.report_quality.policy import (
    IntelligenceInterpretationPolicyBundle,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ConfidenceLevel,
    DerivationStatus,
    LimitationSeverity,
    ReportScope,
)
from codestrata_platform.intelligence_reporting.domain.limitations import DatasetLimitation
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)

_FORBIDDEN_TEXT = (
    "precision/recall",
    "false positive",
    "false negative",
    "maturity score",
    "health score",
    "readiness score",
    "percentile ranking",
    "league table",
    "statistical significance",
    "confidence percentage",
    "probability that the report is correct",
)


def validate_report_quality(
    report: EngineeringIntelligenceReport,
    *,
    diagnostics: ReportQualityDiagnostics,
    bundle: IntelligenceInterpretationPolicyBundle,
    raw_limitation_count: int,
) -> None:
    confidence = report.confidence
    if confidence.level not in set(ConfidenceLevel):
        raise InvalidValueError(
            "invalid report confidence level",
            reason_code="invalid_report_confidence_level",
        )
    if confidence.derivation_status not in set(DerivationStatus):
        raise InvalidValueError(
            "invalid confidence derivation status",
            reason_code="invalid_derivation_status",
        )
    if confidence.comparable_repository_count > confidence.repository_sample_count:
        raise InvalidValueError(
            "comparable count exceeds included sample",
            reason_code="comparable_exceeds_sample",
        )
    if confidence.repository_sample_count != diagnostics.included_repository_count:
        raise InvalidValueError(
            "confidence sample count does not reconcile with diagnostics",
            reason_code="sample_count_mismatch",
        )
    if confidence.comparable_repository_count != diagnostics.comparable_repository_count:
        raise InvalidValueError(
            "comparable count does not reconcile with diagnostics",
            reason_code="comparable_count_mismatch",
        )
    if confidence.level != ConfidenceLevel(diagnostics.report_confidence_level):
        raise InvalidValueError(
            "diagnostics confidence level does not match report confidence",
            reason_code="diagnostics_confidence_mismatch",
        )
    if confidence.level in {ConfidenceLevel.LIMITED, ConfidenceLevel.UNAVAILABLE}:
        if not confidence.limitations and confidence.derivation_status is DerivationStatus.DERIVED:
            raise InvalidValueError(
                "Limited/Unavailable confidence requires limitations",
                reason_code="confidence_limitations_required",
            )
        if not report.limitations:
            raise InvalidValueError(
                "Limited/Unavailable confidence requires dataset limitations",
                reason_code="dataset_limitations_required",
            )

    seen_ids: set[str] = set()
    included = set(report.dataset.included_repository_ids)
    pattern_ids = {item.pattern_id.value for item in report.recurring_patterns}
    observation_ids = {item.observation_id.value for item in report.modernization_observations}
    head_ids = {item.assessment_head_id for item in report.capability_comparisons} | {
        item.assessment_head_id for item in report.assessment_head_distributions
    }

    non_temporal = False
    selection_bias = False
    for limitation in report.limitations:
        _validate_limitation(
            limitation,
            included=included,
            head_ids=head_ids,
            observation_ids=observation_ids | pattern_ids,
            seen_ids=seen_ids,
            report_scope=report.report_scope,
            dataset=report,
        )
        if limitation.category.value == "non_temporal_dataset":
            non_temporal = True
        if limitation.category.value == "selection_bias":
            selection_bias = True
        blob = f"{limitation.statement} {limitation.remediation_or_interpretation or ''}".lower()
        for token in _FORBIDDEN_TEXT:
            if token in blob:
                raise InvalidValueError(
                    f"limitation statement contains prohibited language: {token}",
                    reason_code="forbidden_limitation_language",
                )

    if not non_temporal:
        raise InvalidValueError(
            "non-temporal dataset limitation is required",
            reason_code="missing_non_temporal_limitation",
        )
    if (
        report.report_scope is ReportScope.PUBLIC_OSS_DATASET
        and not selection_bias
    ):
        raise InvalidValueError(
            "public OSS scope requires selection-bias disclosure",
            reason_code="missing_selection_bias_limitation",
        )

    if report.interpretation_policy_bundle_id != bundle.bundle_id:
        raise InvalidValueError(
            "report interpretation_policy_bundle_id does not match bundle",
            reason_code="bundle_id_mismatch",
        )
    if diagnostics.policy_bundle_id != bundle.bundle_id:
        raise InvalidValueError(
            "diagnostics policy_bundle_id does not match bundle",
            reason_code="diagnostics_bundle_mismatch",
        )
    if diagnostics.unresolved_reference_count != 0:
        raise InvalidValueError(
            "unresolved limitation references present",
            reason_code="unresolved_limitation_refs",
        )
    if diagnostics.limitation_count != len(report.limitations):
        raise InvalidValueError(
            "limitation diagnostics count mismatch",
            reason_code="limitation_count_mismatch",
        )
    if diagnostics.deduplicated_limitation_count > raw_limitation_count:
        raise InvalidValueError(
            "deduplicated count cannot exceed raw limitation count",
            reason_code="dedupe_count_invalid",
        )

    # No score/percentage fields on confidence.
    for attr in ("percentage", "probability", "score", "precision", "recall"):
        if hasattr(confidence, attr):
            raise InvalidValueError(
                f"confidence must not expose {attr}",
                reason_code="forbidden_confidence_field",
            )


def _validate_limitation(
    limitation: DatasetLimitation,
    *,
    included: set[str],
    head_ids: set[str],
    observation_ids: set[str],
    seen_ids: set[str],
    report_scope: ReportScope,
    dataset: EngineeringIntelligenceReport,
) -> None:
    if limitation.limitation_id.value in seen_ids:
        raise InvalidValueError(
            "duplicate limitation_id",
            reason_code="duplicate_limitation_id",
        )
    seen_ids.add(limitation.limitation_id.value)
    if limitation.severity not in set(LimitationSeverity):
        raise InvalidValueError(
            "invalid limitation severity",
            reason_code="invalid_limitation_severity",
        )
    missing_repos = set(limitation.affected_repository_ids) - included
    if missing_repos:
        raise InvalidValueError(
            f"limitation references unknown repositories: {sorted(missing_repos)}",
            reason_code="limitation_repo_not_in_dataset",
        )
    missing_heads = set(limitation.affected_assessment_head_ids) - head_ids
    # Heads may be referenced before comparisons are built; allow catalog heads
    # only when capability section is empty.
    if missing_heads and head_ids:
        raise InvalidValueError(
            f"limitation references unknown assessment heads: {sorted(missing_heads)}",
            reason_code="limitation_head_unresolved",
        )
    missing_obs = set(limitation.affected_observation_ids) - observation_ids
    if missing_obs:
        raise InvalidValueError(
            f"limitation references unknown observations/patterns: {sorted(missing_obs)}",
            reason_code="limitation_observation_unresolved",
        )
    if (
        limitation.customer_visible
        and report_scope is ReportScope.PUBLIC_OSS_DATASET
    ):
        private = {
            ref.repository_id
            for ref in dataset.dataset.repository_assessments
            if ref.visibility.value in {"customer_private", "internal"}
        }
        leaked = set(limitation.affected_repository_ids) & private
        if leaked:
            raise InvalidValueError(
                "public-visible limitation must not include private repository IDs",
                reason_code="public_limitation_private_ids",
            )
