"""Approved volatility and forbidden environment-derived fields."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from codestrata.reporting.contract.constants import VOLATILE_JSON_PATHS


@dataclass(frozen=True, slots=True)
class VolatileField:
    field_path: str
    producer: str
    reason: str
    participates_in_ids: bool
    appears_in_customer_artifacts: bool
    normalization: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def approved_volatile_fields() -> list[VolatileField]:
    """Only fields already intended to be volatile by product contract."""

    fields: list[VolatileField] = []
    for path in VOLATILE_JSON_PATHS:
        fields.append(
            VolatileField(
                field_path=path,
                producer="Engine assessment reporting",
                reason="execution timing / generation metadata",
                participates_in_ids=False,
                appears_in_customer_artifacts=True,
                normalization="strip_volatile_fields / SV.4 normalize_report",
            )
        )
    fields.extend(
        [
            VolatileField(
                field_path="manifest.scan_id",
                producer="Engine assessment reporting",
                reason="per-run scan identifier (live acceptance extra path)",
                participates_in_ids=False,
                appears_in_customer_artifacts=True,
                normalization="LIVE_DETERMINISM_EXTRA_PATHS strip",
            ),
            VolatileField(
                field_path="ValidationSummaryArtifact.generated_at",
                producer="Epic 4 validation summary",
                reason="summary generation timestamp",
                participates_in_ids=False,
                appears_in_customer_artifacts=False,
                normalization="canonical_dict pops generated_at",
            ),
            VolatileField(
                field_path="CommunityCloud.request_id",
                producer="Community Cloud HTTP transport",
                reason="transport request id; not event identity material",
                participates_in_ids=False,
                appears_in_customer_artifacts=False,
                normalization="ignored by event fingerprint / key",
            ),
            VolatileField(
                field_path="verification.execution_environment_labels",
                producer="System Verification runners",
                reason="optional local labels; not identity",
                participates_in_ids=False,
                appears_in_customer_artifacts=False,
                normalization="excluded from fingerprints",
            ),
        ]
    )
    return fields


FORBIDDEN_ENVIRONMENT_FIELDS: tuple[str, ...] = (
    "absolute temporary paths",
    "home directory",
    "username",
    "hostname",
    "process ID",
    "random UUIDs where deterministic IDs required",
    "Python object addresses",
    "local timezone in IDs",
    "locale-dependent formatting in IDs",
    "unordered set representation",
    "Git clone directory name (where irrelevant)",
    "developer checkout path",
    "environment variable values",
    "virtual-environment path",
    "OpenTofu executable absolute path in verification report",
)


def build_deterministic_contract_registry() -> list[dict[str, Any]]:
    """Verification-only registry referencing product contracts."""

    return [
        {
            "contract_name": "report.json",
            "producer": "Engine assessment reporting",
            "deterministic_identity_fields": [
                "finding.id",
                "recommendation.id",
                "evidence ids",
                "correlation ids",
            ],
            "approved_volatile_fields": list(VOLATILE_JSON_PATHS),
            "comparison_method": "strip_volatile_fields / reports_structurally_equal",
            "expected_order_behavior": "canonical sorted serialization",
            "round_trip_behavior": "assessment_json_to_text → parse → validate",
        },
        {
            "contract_name": "findings.json",
            "producer": "Engine assessment reporting",
            "deterministic_identity_fields": ["finding.id"],
            "comparison_method": "ID sets + ordered companion reconcile",
            "expected_order_behavior": "stable sort by contract keys",
        },
        {
            "contract_name": "recommendations.json",
            "producer": "Engine assessment reporting",
            "deterministic_identity_fields": [
                "recommendation.id",
                "supporting_finding_ids",
            ],
            "comparison_method": "ID sets + ordered companion reconcile",
        },
        {
            "contract_name": "report.html",
            "producer": "Engine HTML renderer",
            "deterministic_identity_fields": ["anchors", "TOC order"],
            "comparison_method": "normalize_html / html_fingerprint (SV.5)",
            "approved_volatile_fields": ["narrow HTML timing if any"],
        },
        {
            "contract_name": "validation_record",
            "producer": "Epic 4 recorder",
            "deterministic_identity_fields": ["run_id", "fp_id", "fn_id"],
            "comparison_method": "load → stable form",
        },
        {
            "contract_name": "validation_summary",
            "producer": "Epic 4 summary",
            "deterministic_identity_fields": ["pack counts", "metric ids"],
            "comparison_method": "canonical_dict without generated_at",
        },
        {
            "contract_name": "IntelligenceDataset",
            "producer": "Platform EI ingestion",
            "deterministic_identity_fields": ["dataset_id"],
            "expected_order_behavior": "order-independent across assessment inputs",
        },
        {
            "contract_name": "CrossRepositoryAggregation",
            "producer": "Platform EI aggregation",
            "deterministic_identity_fields": ["aggregation_id"],
            "expected_order_behavior": "order-independent",
        },
        {
            "contract_name": "EngineeringIntelligenceReport",
            "producer": "Platform EI pipeline",
            "deterministic_identity_fields": [
                "report_id",
                "interpretation_policy_bundle_id",
            ],
            "round_trip_behavior": "report_to_stable_dict ↔ from_stable_dict",
        },
        {
            "contract_name": "website_safe_export",
            "producer": "Platform website export",
            "deterministic_identity_fields": ["export_id", "sha256 digests"],
            "comparison_method": "byte-for-byte JSON/HTML/manifest",
            "expected_order_behavior": "no output-directory influence",
        },
        {
            "contract_name": "community_cloud_responses",
            "producer": "Community Cloud API",
            "deterministic_identity_fields": [
                "event key",
                "payload fingerprint",
                "safe event reference",
            ],
            "comparison_method": "in-memory adapters + SequenceClock",
        },
        {
            "contract_name": "infrastructure_verification",
            "producer": "SV.9 infrastructure verification",
            "deterministic_identity_fields": ["verdict", "check vector"],
            "comparison_method": "repeated check_structure",
        },
        {
            "contract_name": "system_verification_reports",
            "producer": "SV.2–SV.14 packages",
            "deterministic_identity_fields": [
                "schema_name",
                "schema_version",
                "verdict",
            ],
            "comparison_method": "stable JSON serialization fingerprints",
        },
    ]
