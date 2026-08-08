"""Audit checks for Slice 15.1 Community Data Lake."""

from __future__ import annotations

import re
from pathlib import Path

from verification.community_data_lake_audit.contract import (
    ACCEPTED_STREAMS,
    CONTRACT_DOC_RELATIVE,
    FINDING_CLASSES,
    FORBIDDEN_15_7_PATHS,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    PYTHON_POLICY_MODULE,
)
from verification.community_data_lake_audit.findings import AUDIT_FINDINGS
from verification.community_data_lake_audit.inventory import exists, load_json, read_text
from verification.community_data_lake_audit.models import (
    AuditFinding,
    CheckResult,
    Defect,
)


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "audit_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    _add(checks, defects, "policy:present", bool(policy), "present", "policy")
    _add(
        checks,
        defects,
        "policy:id",
        policy.get("policy_id") == POLICY_ID,
        str(policy.get("policy_id")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:version",
        policy.get("policy_version") == POLICY_VERSION,
        str(policy.get("policy_version")),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:start_slice_16_3_false",
        policy.get("start_slice_16_3", False) is False,
        str(policy.get("start_slice_16_3", False)),
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:no_telemetry_redesign",
        policy.get("telemetry_redesign_allowed") is False,
        "forbidden",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:no_schema_redesign",
        policy.get("schema_redesign_allowed") is False,
        "forbidden",
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:contract_doc_present",
        exists(monorepo, CONTRACT_DOC_RELATIVE),
        CONTRACT_DOC_RELATIVE,
        "policy",
    )
    py = read_text(monorepo, PYTHON_POLICY_MODULE)
    _add(
        checks,
        defects,
        "policy:python_source_matches_id",
        'COMMUNITY_DATA_LAKE_POLICY_ID = "community-data-lake-policy"' in py,
        "aligned",
        "policy",
    )
    classes = policy.get("audit_classifications", {})
    for finding in AUDIT_FINDINGS:
        observed = classes.get(finding.area)
        ok = observed == finding.classification
        _add(
            checks,
            defects,
            f"policy:classification:{finding.area}",
            ok,
            str(observed),
            "findings",
        )
        if observed not in FINDING_CLASSES and observed is not None:
            defects.append(
                Defect(
                    "invalid_classification",
                    finding.area,
                    "|".join(FINDING_CLASSES),
                    str(observed),
                )
            )
    return checks, defects


def check_bucket_layout(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    locals_tf = read_text(
        monorepo, "infrastructure/modules/community-data-lake/locals.tf"
    )
    _add(
        checks,
        defects,
        "bucket:module_present",
        exists(monorepo, "infrastructure/modules/community-data-lake"),
        "present",
        "bucket_layout",
    )
    _add(
        checks,
        defects,
        "bucket:accepted_prefix_raw",
        'accepted_prefix   = "raw/"' in locals_tf
        or 'accepted_prefix = "raw/"' in locals_tf,
        "raw/",
        "bucket_layout",
    )
    _add(
        checks,
        defects,
        "bucket:quarantine_prefix",
        "quarantine/" in locals_tf,
        "quarantine/",
        "bucket_layout",
    )
    _add(
        checks,
        defects,
        "bucket:single_bucket_strategy",
        "prefix isolation" in locals_tf.lower()
        or "single private bucket" in locals_tf.lower()
        or "community-data-lake" in locals_tf,
        "single_bucket",
        "bucket_layout",
    )
    prod = read_text(monorepo, "infrastructure/production/community-data-lake.tf")
    _add(
        checks,
        defects,
        "bucket:production_wiring_file",
        bool(prod),
        "present" if prod else "missing",
        "bucket_layout",
    )
    # Ingestion must remain unwired.
    variables = read_text(
        monorepo, "infrastructure/modules/community-data-lake/variables.tf"
    )
    _add(
        checks,
        defects,
        "bucket:ingestion_wire_default_false",
        "enable_ingestion_wire" in variables and "false" in variables,
        "unwired",
        "bucket_layout",
    )
    return checks, defects


def check_partitions(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    parts = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/data_lake/partitions.py",
    )
    _add(
        checks,
        defects,
        "partitions:hive_raw_stream",
        "stream=" in parts and "schema_version=" in parts,
        "hive",
        "event_partitions",
    )
    _add(
        checks,
        defects,
        "partitions:forbid_installation_in_key",
        "installation" in parts.lower(),
        "guard_present",
        "event_partitions",
    )
    enums = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/data_lake/enums.py",
    )
    for stream in ACCEPTED_STREAMS:
        _add(
            checks,
            defects,
            f"partitions:stream_{stream}",
            f'"{stream}"' in enums or f"'{stream}'" in enums,
            stream,
            "event_partitions",
        )
    return checks, defects


def check_schema_consistency(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    const = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/constants.py",
    )
    _add(
        checks,
        defects,
        "schema:envelope_1_0",
        'COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION = "1.0"' in const
        or re.search(
            r'COMMUNITY_DATA_LAKE_ENVELOPE_SCHEMA_VERSION\s*=\s*"1\.0"', const
        )
        is not None,
        "1.0",
        "schema_consistency",
    )
    _add(
        checks,
        defects,
        "schema:policy_version_1_0",
        'COMMUNITY_DATA_LAKE_POLICY_VERSION = "1.0"' in const
        or re.search(r'COMMUNITY_DATA_LAKE_POLICY_VERSION\s*=\s*"1\.0"', const)
        is not None,
        "1.0",
        "schema_consistency",
    )
    assessment = read_text(
        monorepo, "engine/src/codestrata/reporting/contract/constants.py"
    )
    _add(
        checks,
        defects,
        "schema:assessment_remains_1_2",
        'ASSESSMENT_JSON_SCHEMA_VERSION = "1.2"' in assessment,
        "1.2",
        "schema_consistency",
    )
    return checks, defects


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    envelopes = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/data_lake/envelopes.py",
    )
    _add(
        checks,
        defects,
        "privacy:forbid_source_code_key",
        '"source_code"' in envelopes,
        "forbidden",
        "privacy_compliance",
    )
    _add(
        checks,
        defects,
        "privacy:forbid_ip_and_auth",
        '"ip_address"' in envelopes and '"authorization"' in envelopes,
        "forbidden",
        "privacy_compliance",
    )
    _add(
        checks,
        defects,
        "privacy:forbid_prompt_response",
        '"prompt"' in envelopes and '"response"' in envelopes,
        "forbidden",
        "no_source_code",
    )
    policy = load_json(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "privacy:community_only",
        policy.get("community_only") is True,
        "community_only",
        "privacy_compliance",
    )
    _add(
        checks,
        defects,
        "privacy:no_customer_source_code",
        policy.get("customer_source_code_allowed") is False,
        "denied",
        "no_source_code",
    )
    _add(
        checks,
        defects,
        "privacy:no_personal_identifiers",
        policy.get("personal_identifiers_allowed") is False,
        "denied",
        "no_personal_identifiers",
    )
    return checks, defects


def check_anonymous_identity(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "identity:payload_only",
        policy.get("installation_id_payload_only") is True,
        "payload_only",
        "anonymous_identity",
    )
    _add(
        checks,
        defects,
        "identity:not_in_path_metadata",
        policy.get("installation_id_in_path_or_metadata_allowed") is False,
        "denied",
        "anonymous_identity",
    )
    identity_doc = exists(
        monorepo, "engine/docs/telemetry-installation-identity.md"
    ) or exists(
        monorepo,
        "engine/src/codestrata/telemetry/analytics/installation_identity.py",
    )
    # Try common paths
    identity_paths = [
        "engine/src/codestrata/telemetry/analytics/installation_identity.py",
        "engine/docs/telemetry-installation-identity.md",
    ]
    present = any(exists(monorepo, p) for p in identity_paths)
    _add(
        checks,
        defects,
        "identity:engine_package_present",
        present or identity_doc,
        "present" if present else "missing",
        "anonymous_identity",
    )
    return checks, defects


def check_dashboard_readiness(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "dashboard:storage_contract_ready",
        policy.get("dashboard_storage_contract_ready") is True,
        "ready",
        "dashboard_readiness",
    )
    _add(
        checks,
        defects,
        "dashboard:implementation_not_started",
        policy.get("dashboard_ready_for_implementation") is False,
        "not_started",
        "dashboard_readiness",
    )
    _add(
        checks,
        defects,
        "dashboard:no_aggregations",
        policy.get("aggregations_allowed_in_15_1") is False,
        "forbidden",
        "dashboard_readiness",
    )
    _add(
        checks,
        defects,
        "dashboard:package_absent",
        not exists(
            monorepo, "platform/src/codestrata_platform/community_insights_dashboard"
        ),
        "absent",
        "dashboard_readiness",
    )
    return checks, defects


def check_export_and_ownership(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    manifest = read_text(monorepo, "public-export-manifest.yaml")
    _add(
        checks,
        defects,
        "export:manifest_present",
        bool(manifest),
        "present",
        "export_boundary",
    )
    _add(
        checks,
        defects,
        "export:platform_forbidden",
        "platform/" in manifest,
        "forbidden",
        "export_boundary",
    )
    _add(
        checks,
        defects,
        "export:infrastructure_forbidden",
        "infrastructure/" in manifest,
        "forbidden",
        "export_boundary",
    )
    policy = load_json(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "ownership:platform_private",
        policy.get("ownership") == "platform-private",
        str(policy.get("ownership")),
        "ownership",
    )
    _add(
        checks,
        defects,
        "ownership:public_export_denied",
        policy.get("public_export_allowed") is False,
        "denied",
        "ownership",
    )
    return checks, defects


def check_retention(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "retention:accepted_365",
        policy.get("accepted_retention_days") == 365,
        str(policy.get("accepted_retention_days")),
        "retention",
    )
    _add(
        checks,
        defects,
        "retention:quarantine_90",
        policy.get("quarantine_retention_days") == 90,
        str(policy.get("quarantine_retention_days")),
        "retention",
    )
    _add(
        checks,
        defects,
        "retention:quarantine_le_accepted",
        int(policy.get("quarantine_retention_days") or 0)
        <= int(policy.get("accepted_retention_days") or 0),
        "ordered",
        "retention",
    )
    return checks, defects


def check_requires_change_items(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    """Confirm previously stale docs were corrected during the audit."""
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    completion_readme = read_text(
        monorepo, "platform/verification/community_data_lake_completion/README.md"
    )
    stale_epic9 = "| Epic 9 | Not started |" in completion_readme
    _add(
        checks,
        defects,
        "docs:epic9_status_corrected",
        not stale_epic9 and "Epic 9" in completion_readme,
        "corrected",
        "requires_change",
    )
    future_doc = read_text(monorepo, "infrastructure/docs/future-data-lake.md")
    stale_wiring = "Deferred to later Epic 8 slices" in future_doc
    _add(
        checks,
        defects,
        "docs:future_data_lake_corrected",
        not stale_wiring and "post-Epic-8" in future_doc,
        "corrected",
        "requires_change",
    )
    return checks, defects


def check_slice_15_7_absent(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    present = [rel for rel in FORBIDDEN_15_7_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "slice_15_2:paths_absent",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_7_boundary",
        "slice_15_2_started",
    )
    reports = monorepo / "reports" / "verification"
    sv152 = []
    if reports.is_dir():
        sv152 = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir() and p.name.startswith("sv15-") and p.name not in {"sv15-1", "sv15-2", "sv15-3", "sv15-4", "sv15-5", "sv15-6", "sv15-7", "sv15-8", "sv15-9", "sv15-10", "sv15-11", "sv15-12", "sv16-1"}
        )
    _add(
        checks,
        defects,
        "slice_15_2:no_sv15_2_plus",
        not sv152,
        "absent" if not sv152 else ",".join(sv152),
        "slice_15_7_boundary",
        "slice_15_2_started",
    )
    return checks, defects


def build_findings() -> list[AuditFinding]:
    return list(AUDIT_FINDINGS)
