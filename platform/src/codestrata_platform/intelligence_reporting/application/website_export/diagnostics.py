"""WebsiteExportDiagnostics — factual counters only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WebsiteExportDiagnostics:
    repository_count: int = 0
    exported_repository_count: int = 0
    anonymized_repository_count: int = 0
    omitted_repository_count: int = 0
    section_count: int = 0
    entity_ref_count: int = 0
    json_byte_count: int = 0
    html_byte_count: int = 0
    anchor_count: int = 0
    unresolved_anchor_count: int = 0
    unsafe_value_count: int = 0
    rejected_field_count: int = 0
    truncation_count: int = 0
    export_id: str = ""
    policy_bundle_id: str = ""
    limitations: tuple[str, ...] = ()
