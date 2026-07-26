"""Report contract package (Phase 5.12)."""

from aimf.reporting.contract.canonical import (
    reports_structurally_equal,
    strip_volatile_fields,
)
from aimf.reporting.contract.constants import (
    ASSESSMENT_JSON_REPORT_VERSION,
    ASSESSMENT_JSON_SCHEMA_VERSION,
    REPORT_CONTRACT_VERSION,
    REPORT_HTML_VERSION,
    VOLATILE_JSON_PATHS,
)
from aimf.reporting.contract.enums import (
    normalize_confidence,
    normalize_effort,
    normalize_priority,
    normalize_risk,
    normalize_severity,
    normalize_status,
)
from aimf.reporting.contract.identifiers import (
    build_finding_id_map,
    stable_finding_id,
    stable_recommendation_id,
)
from aimf.reporting.contract.manifest import build_report_manifest
from aimf.reporting.contract.ordering import (
    dedupe_by_id,
    sorted_evidence,
    sorted_findings,
    sorted_recommendations,
    sorted_technologies,
)

__all__ = [
    "ASSESSMENT_JSON_REPORT_VERSION",
    "ASSESSMENT_JSON_SCHEMA_VERSION",
    "REPORT_CONTRACT_VERSION",
    "REPORT_HTML_VERSION",
    "VOLATILE_JSON_PATHS",
    "build_finding_id_map",
    "build_report_manifest",
    "dedupe_by_id",
    "normalize_confidence",
    "normalize_effort",
    "normalize_priority",
    "normalize_risk",
    "normalize_severity",
    "normalize_status",
    "reports_structurally_equal",
    "sorted_evidence",
    "sorted_findings",
    "sorted_recommendations",
    "sorted_technologies",
    "stable_finding_id",
    "stable_recommendation_id",
    "strip_volatile_fields",
]
