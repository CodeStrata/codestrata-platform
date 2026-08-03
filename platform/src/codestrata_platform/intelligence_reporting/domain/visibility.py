"""Visibility controls and website-safe export policy (no renderer)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    optional_sorted_ids,
    reject_unsafe_text,
)
from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility

_FORBIDDEN_EXPORT_KEYS = frozenset(
    {
        "source_body",
        "snippet",
        "excerpt",
        "raw_evidence",
        "absolute_path",
        "file_path",
        "password",
        "secret",
        "private_key",
        "credential",
        "customer_id",
        "temporary_path",
    }
)


@dataclass(frozen=True, slots=True)
class WebsiteExportPolicy:
    """Policy describing what a later website export may include."""

    allow_public_repository_names: bool = True
    allow_public_repository_urls: bool = True
    allow_aggregated_counts: bool = True
    allow_safe_technologies: bool = True
    allow_safe_rule_labels: bool = True
    allow_anonymized_repository_identifiers: bool = True
    allow_bounded_observations: bool = True
    allow_methodology: bool = True
    allow_confidence: bool = True
    allow_dataset_limitations: bool = True
    forbid_source_bodies: bool = True
    forbid_snippets: bool = True
    forbid_raw_evidence_payloads: bool = True
    forbid_absolute_paths: bool = True
    forbid_private_repository_names: bool = True
    forbid_credentials: bool = True
    forbid_secret_fingerprints: bool = True
    forbid_customer_identifiers: bool = True
    forbid_internal_platform_ids_when_unsafe: bool = True
    forbid_temporary_artifact_paths: bool = True
    forbid_private_source_urls: bool = True
    preferred_visibility_mode: DataVisibility = DataVisibility.ANONYMIZED

    @classmethod
    def public_default(cls) -> WebsiteExportPolicy:
        return cls(preferred_visibility_mode=DataVisibility.PUBLIC)

    @classmethod
    def anonymized_default(cls) -> WebsiteExportPolicy:
        return cls(
            allow_public_repository_names=False,
            allow_public_repository_urls=False,
            preferred_visibility_mode=DataVisibility.ANONYMIZED,
        )

    def assert_payload_safe(self, payload: Mapping[str, object]) -> None:
        blob_keys = {str(key).lower() for key in payload}
        forbidden = sorted(blob_keys & _FORBIDDEN_EXPORT_KEYS)
        if forbidden:
            raise InvalidValueError(
                f"website export payload contains forbidden keys: {', '.join(forbidden)}",
                reason_code="website_export_forbidden_keys",
            )
        text = str(payload)
        reject_unsafe_text(text[:4000] if len(text) > 4000 else text, label="export_payload")


@dataclass(frozen=True, slots=True)
class WebsiteSafeIntelligenceReport:
    """Export-oriented view constrained by WebsiteExportPolicy (no HTML)."""

    report_id: str
    schema_version: str
    report_scope: str
    dataset_id: str
    visibility_mode: str
    included_repository_ids: tuple[str, ...] = ()
    public_repository_ids: tuple[str, ...] = ()
    anonymized_repository_ids: tuple[str, ...] = ()
    public_repository_display_names: tuple[str, ...] = ()
    aggregated_counts: Mapping[str, int] = field(default_factory=dict)
    safe_technology_names: tuple[str, ...] = ()
    safe_observation_titles: tuple[str, ...] = ()
    methodology_notes: tuple[str, ...] = ()
    confidence_level: str | None = None
    customer_visible_limitations: tuple[str, ...] = ()
    policy: WebsiteExportPolicy = field(default_factory=WebsiteExportPolicy)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "included_repository_ids",
            optional_sorted_ids(self.included_repository_ids, label="included_repository_id"),
        )
        object.__setattr__(
            self,
            "public_repository_ids",
            optional_sorted_ids(self.public_repository_ids, label="public_repository_id"),
        )
        object.__setattr__(
            self,
            "anonymized_repository_ids",
            optional_sorted_ids(
                self.anonymized_repository_ids, label="anonymized_repository_id"
            ),
        )
        object.__setattr__(
            self,
            "public_repository_display_names",
            optional_sorted_ids(
                self.public_repository_display_names, label="public_repository_display_name"
            ),
        )
        object.__setattr__(
            self,
            "safe_technology_names",
            optional_sorted_ids(self.safe_technology_names, label="safe_technology_name"),
        )
        object.__setattr__(
            self,
            "safe_observation_titles",
            optional_sorted_ids(self.safe_observation_titles, label="safe_observation_title"),
        )
        object.__setattr__(
            self,
            "methodology_notes",
            optional_sorted_ids(self.methodology_notes, label="methodology_note"),
        )
        object.__setattr__(
            self,
            "customer_visible_limitations",
            optional_sorted_ids(
                self.customer_visible_limitations, label="customer_visible_limitation"
            ),
        )
        object.__setattr__(
            self,
            "aggregated_counts",
            dict(sorted((str(k), int(v)) for k, v in self.aggregated_counts.items())),
        )

    def to_stable_dict(self) -> dict[str, object]:
        from codestrata_platform.intelligence_reporting.domain.serialization import (
            to_stable_dict,
        )

        return to_stable_dict(self)
