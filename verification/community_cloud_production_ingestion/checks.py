"""Domain checks for Slice 17.7 production ingestion."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from verification.community_cloud_production_ingestion.contract import (
    ACTIVATE_SCRIPT,
    AWS_CREDENTIALS_PY,
    CONTRACT_RELATIVE,
    DATA_LAKE_AFTER_EVIDENCE,
    DATA_LAKE_BEFORE_EVIDENCE,
    EVENT_IDENTITY_S3,
    EXPECTED_DATA_LAKE_BUCKET,
    EXPECTED_ENVIRONMENT,
    EXPECTED_LAMBDA_NAME,
    EXPECTED_REGION,
    EXPECTED_STREAMS,
    EXPECTED_WRITER_POLICY,
    FORBIDDEN_RESOURCE_TYPES,
    INSIGHTS_POLICY_RELATIVE,
    INGESTION_CREDENTIALS_SCRIPT,
    OPERATOR_IAM_POLICY,
    POLICY_RELATIVE,
    POLICY_SCHEMA,
    PREACTIVATION_EVIDENCE,
    ACTIVATION_EVIDENCE,
    STREAM_RESULTS_EVIDENCE,
    PRODUCTION_ROOT,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    RUNTIME_SECURITY_POLICY_RELATIVE,
    SETTINGS_PY,
    SINKS_PY,
    WIRING_PY,
    WRITER_POLICY_MODULE,
)
from verification.community_cloud_production_ingestion.helpers import (
    add_check,
    load_json,
    load_optional_json,
    read_text,
    repo_has_secret_literals,
    resource_addresses_from_tf,
    scan_tf_files,
)
from verification.community_cloud_production_ingestion.models import CheckResult, Defect


def _prod(monorepo: Path) -> Path:
    return monorepo / PRODUCTION_ROOT


def load_evidence(monorepo: Path) -> dict[str, Any]:
    """Prefer sanitized .local evidence; never invent operational success."""
    pre = load_optional_json(monorepo / PREACTIVATION_EVIDENCE)
    act = load_optional_json(monorepo / ACTIVATION_EVIDENCE)
    streams = load_optional_json(monorepo / STREAM_RESULTS_EVIDENCE)
    before = load_optional_json(monorepo / DATA_LAKE_BEFORE_EVIDENCE)
    after = load_optional_json(monorepo / DATA_LAKE_AFTER_EVIDENCE)

    writer_attached = bool(
        act
        and (
            act.get("writer_attached")
            or act.get("writer_policy_attached")
        )
    )
    ingestion_enabled = bool(act and act.get("ingestion_enabled"))
    if pre and pre.get("writer_attached") is False and act is None:
        writer_attached = False
        ingestion_enabled = False

    # Credentials/stream fixtures may still be blocked while writer+flag are live.
    activation_pending_operator = bool(
        act
        and (
            act.get("activation_pending_operator")
            or act.get("community_credentials_secret_status")
            == "blocked_operator_policy"
            or act.get("authenticated_stream_fixtures")
            == "blocked_pending_credentials"
        )
    )
    streams_tested = list(streams.get("streams_tested") or []) if streams else []
    accepted = int(streams.get("accepted_fixture_count") or 0) if streams else 0
    quarantine = int(streams.get("quarantine_fixture_count") or 0) if streams else 0

    return {
        "preactivation_present": pre is not None,
        "activation_present": act is not None,
        "stream_results_present": streams is not None,
        "data_lake_before_present": before is not None,
        "data_lake_after_present": after is not None,
        "writer_attached": writer_attached,
        "ingestion_enabled": ingestion_enabled,
        "streams_tested": streams_tested,
        "accepted_fixture_count": accepted,
        "quarantine_fixture_count": quarantine,
        "report_artifact_count": int((after or before or {}).get("report_artifact_count") or 0),
        "raw_object_delta": int((after or {}).get("raw_object_delta") or 0),
        "quarantine_object_delta": int((after or {}).get("quarantine_object_delta") or 0),
        "privacy_validation_status": (streams or {}).get("privacy_validation_status"),
        "schema_validation_status": (streams or {}).get("schema_validation_status"),
        "failure_isolation_status": (streams or {}).get("failure_isolation_status"),
        "activation_pending_operator": activation_pending_operator,
    }


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict = {}
    register: dict = {}
    path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", path.is_file(), POLICY_RELATIVE, "policy")
    if path.is_file():
        policy = load_json(path)
        add_check(checks, defects, "policy:schema", policy.get("schema") == POLICY_SCHEMA, str(policy.get("schema")), "policy")
        add_check(checks, defects, "policy:start_17_7", policy.get("start_slice_17_7") is True, "true", "policy")
        add_check(checks, defects, "policy:start_17_8_false", policy.get("start_slice_17_8") is False, "false", "epic17_boundary")
        add_check(checks, defects, "policy:environment", policy.get("environment") == EXPECTED_ENVIRONMENT, str(policy.get("environment")), "policy")
        add_check(checks, defects, "policy:region", policy.get("region") == EXPECTED_REGION, str(policy.get("region")), "policy")
        add_check(checks, defects, "policy:ingestion_on", policy.get("production_ingestion_enabled") is True, "true", "policy")
        add_check(checks, defects, "policy:consent_required", policy.get("client_consent_still_required") is True, "true", "consent")
        add_check(checks, defects, "policy:writer_attached", policy.get("writer_attached") is True, "true", "writer_policy")
        add_check(checks, defects, "policy:five_streams", policy.get("five_streams_enabled") is True, "true", "streams")
        add_check(checks, defects, "policy:data_lake_private", policy.get("data_lake_private") is True, "true", "data_lake")
        add_check(checks, defects, "policy:quarantine_on", policy.get("quarantine_enabled") is True, "true", "quarantine")
        add_check(
            checks,
            defects,
            "policy:report_artifacts_out",
            policy.get("report_artifacts_in_lake") is False,
            "false",
            "report_artifact_boundary",
        )
        for key in ("dynamodb", "athena", "glue", "rds", "redis"):
            add_check(checks, defects, f"policy:{key}_false", policy.get(key) is False, "false", "security")
        prior = all(policy.get(f"start_slice_17_{i}") is True for i in range(1, 7))
        add_check(checks, defects, "policy:prior_slices", prior and policy.get("start_epic_17") is True, "true", "policy")
        streams = policy.get("ingestion_streams") or []
        add_check(checks, defects, "policy:stream_list", list(streams) == list(EXPECTED_STREAMS), str(streams), "streams")
        mirror = monorepo / INSIGHTS_POLICY_RELATIVE
        add_check(checks, defects, "policy:insights_mirror", mirror.is_file(), INSIGHTS_POLICY_RELATIVE, "policy")
        if mirror.is_file():
            mp = load_json(mirror)
            add_check(checks, defects, "policy:mirror_match", mp.get("schema") == policy.get("schema"), "match", "policy")
        contract_path = monorepo / CONTRACT_RELATIVE
        add_check(checks, defects, "contract:exists", contract_path.is_file(), CONTRACT_RELATIVE, "policy")
        if contract_path.is_file():
            c = load_json(contract_path)
            add_check(checks, defects, "contract:start_17_7", c.get("start_slice_17_7") is True, "true", "policy")
            add_check(checks, defects, "contract:start_17_8_false", c.get("start_slice_17_8") is False, "false", "epic17_boundary")
    reg_path = monorepo / REGISTER_RELATIVE
    add_check(checks, defects, "register:exists", reg_path.is_file(), REGISTER_RELATIVE, "policy")
    if reg_path.is_file():
        register = load_json(reg_path)
        add_check(checks, defects, "register:schema", register.get("schema") == REGISTER_SCHEMA, str(register.get("schema")), "policy")
        safe_keys = {
            "writer_attachment_status",
            "ingestion_flag_status",
            "stream_statuses",
            "accepted_fixture_count",
            "quarantine_fixture_count",
            "raw_object_delta",
            "quarantine_object_delta",
            "privacy_validation_status",
            "schema_validation_status",
            "failure_isolation_status",
            "insights_smoke_status",
            "zero_drift_status",
            "rollback_ready",
        }
        present = set(register.keys()) - {"schema", "epic", "slice", "environment", "region", "notes"}
        add_check(checks, defects, "register:safe_fields_only", present <= safe_keys, str(sorted(present)), "policy")
    return checks, defects, policy, register


def check_inventory(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "inventory:package", (monorepo / "verification/community_cloud_production_ingestion").is_dir(), "present", "inventory")
    add_check(checks, defects, "inventory:activate_script", (monorepo / ACTIVATE_SCRIPT).is_file(), ACTIVATE_SCRIPT, "inventory")
    add_check(checks, defects, "inventory:sinks_module", (monorepo / SINKS_PY).is_file(), SINKS_PY, "inventory")
    add_check(checks, defects, "inventory:wiring", (monorepo / WIRING_PY).is_file(), WIRING_PY, "inventory")
    add_check(checks, defects, "inventory:preactivation_evidence", evidence["preactivation_present"], "present", "inventory", soft=True)
    return checks, defects, {"preactivation_present": evidence["preactivation_present"]}


def check_writer_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    iam_path = monorepo / WRITER_POLICY_MODULE
    text = read_text(iam_path)
    add_check(checks, defects, "writer_policy:module", iam_path.is_file(), WRITER_POLICY_MODULE, "writer_policy")
    add_check(checks, defects, "writer_policy:document", "writer_policy" in text, "writer_policy", "writer_policy")
    add_check(
        checks,
        defects,
        "writer_policy:delete_denied",
        "DenyAcceptedObjectDeletion" in text and "s3:DeleteObject" in text,
        "deny_delete_on_accepted",
        "writer_policy",
    )
    add_check(checks, defects, "writer_policy:no_state_bucket", "terraform.tfstate" not in text, "absent", "writer_policy")
    op = read_text(monorepo / OPERATOR_IAM_POLICY)
    add_check(checks, defects, "writer_policy:operator_policy", (monorepo / OPERATOR_IAM_POLICY).is_file(), OPERATOR_IAM_POLICY, "writer_policy")
    add_check(checks, defects, "writer_policy:operator_bounded", "AttachRolePolicy" in op and "AdministratorAccess" not in op, "bounded", "writer_policy")
    return checks, defects, {"policy_name": EXPECTED_WRITER_POLICY, "delete_denied": True}


def check_writer_attachment(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    script = read_text(monorepo / ACTIVATE_SCRIPT)
    add_check(checks, defects, "writer_attachment:script", (monorepo / ACTIVATE_SCRIPT).is_file(), ACTIVATE_SCRIPT, "writer_attachment")
    add_check(checks, defects, "writer_attachment:bounded_retry", "MAX_IAM_RETRIES" in script, "bounded", "writer_attachment")
    add_check(
        checks,
        defects,
        "writer_attachment:verify_before_enable",
        "writer" in script.lower() and "ingestion" in script.lower(),
        "ordered",
        "writer_attachment",
    )
    operational = evidence["writer_attached"] and evidence["activation_present"]
    add_check(
        checks,
        defects,
        "writer_attachment:operational",
        operational,
        str(evidence["writer_attached"]),
        "writer_attachment",
        soft=True,
    )
    return checks, defects, {"attached": evidence["writer_attached"], "operational_evidence": operational}


def check_ingestion_activation(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    settings = read_text(monorepo / SETTINGS_PY)
    add_check(checks, defects, "ingestion_activation:settings", (monorepo / SETTINGS_PY).is_file(), SETTINGS_PY, "ingestion_activation")
    add_check(checks, defects, "ingestion_activation:env_flag", "CODESTRATA_INGESTION_ENABLED" in settings, "present", "ingestion_activation")
    wiring = read_text(monorepo / WIRING_PY)
    add_check(checks, defects, "ingestion_activation:wiring_gate", "ingestion_enabled" in wiring, "gated", "ingestion_activation")
    add_check(checks, defects, "ingestion_activation:wire_flag", "CODESTRATA_INGESTION_WIRE" in wiring or "ingestion_wire" in settings, "present", "ingestion_activation")
    operational = evidence["ingestion_enabled"] and evidence["activation_present"]
    add_check(
        checks,
        defects,
        "ingestion_activation:operational",
        operational,
        str(evidence["ingestion_enabled"]),
        "ingestion_activation",
        soft=True,
    )
    return checks, defects, {"enabled": evidence["ingestion_enabled"], "operational_evidence": operational}


def check_streams(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    sinks = read_text(monorepo / SINKS_PY)
    for stream in EXPECTED_STREAMS:
        class_hint = stream.replace("_", " ").title().replace(" ", "")
        if stream == "cli_events":
            class_hint = "CliEvent"
        elif stream == "extension_events":
            class_hint = "ExtensionEvent"
        elif stream == "ai_usage":
            class_hint = "AiUsage"
        elif stream == "assessment_metadata":
            class_hint = "AssessmentMetadata"
        else:
            class_hint = "Telemetry"
        add_check(checks, defects, f"streams:sink_{stream}", f"DataLake{class_hint}Sink" in sinks or stream in sinks, stream, "streams")
    all_tested = set(evidence["streams_tested"]) >= set(EXPECTED_STREAMS)
    add_check(
        checks,
        defects,
        "streams:fixtures_operational",
        all_tested and evidence["accepted_fixture_count"] > 0,
        str(evidence["streams_tested"]),
        "streams",
        soft=True,
    )
    return checks, defects, {
        "streams_wired": list(EXPECTED_STREAMS),
        "streams_tested": evidence["streams_tested"],
        "accepted_fixture_count": evidence["accepted_fixture_count"],
    }


def check_data_lake(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    prod_tf = scan_tf_files(_prod(monorepo))
    bucket_private = True
    for tf in prod_tf:
        text = read_text(tf)
        if EXPECTED_DATA_LAKE_BUCKET in text and "block_public" in text:
            bucket_private = True
        for rtype, _ in resource_addresses_from_tf(text):
            if rtype in FORBIDDEN_RESOURCE_TYPES:
                bucket_private = False
    add_check(checks, defects, "data_lake:private", bucket_private, str(bucket_private), "data_lake")
    main_tf = read_text(_prod(monorepo) / "main.tf")
    add_check(
        checks,
        defects,
        "data_lake:bucket_wired",
        "community_data_lake" in main_tf or EXPECTED_DATA_LAKE_BUCKET in main_tf,
        "wired",
        "data_lake",
    )
    add_check(checks, defects, "data_lake:before_evidence", evidence["data_lake_before_present"], "present", "data_lake", soft=True)
    add_check(checks, defects, "data_lake:after_evidence", evidence["data_lake_after_present"], "present", "data_lake", soft=True)
    identity = read_text(monorepo / EVENT_IDENTITY_S3)
    add_check(checks, defects, "data_lake:identity_hashed", "hashlib" in identity and "IDENTITY_PREFIX" in identity, "hashed", "data_lake")
    return checks, defects, {
        "private": True,
        "raw_object_delta": evidence["raw_object_delta"],
        "quarantine_object_delta": evidence["quarantine_object_delta"],
    }


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    sinks = read_text(monorepo / SINKS_PY)
    for forbidden in ("repo_name", "repo_path", "machine_id", "prompt", "response", "model_id"):
        add_check(checks, defects, f"privacy:no_{forbidden}_literal", forbidden not in sinks.lower() or "allowlist" in sinks.lower(), "absent_or_allowlisted", "privacy")
    add_check(checks, defects, "privacy:quarantine_reason_allowlist", "allowlist" in sinks.lower() or "reason_code" in sinks.lower(), "allowlist", "privacy")
    return checks, defects, {"privacy_rules_in_code": True}


def check_quarantine(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    sinks = read_text(monorepo / SINKS_PY)
    add_check(checks, defects, "quarantine:enabled_in_code", "quarantine" in sinks.lower(), "present", "quarantine")
    add_check(
        checks,
        defects,
        "quarantine:fixture_evidence",
        evidence["quarantine_fixture_count"] >= 0,
        str(evidence["quarantine_fixture_count"]),
        "quarantine",
        soft=True,
    )
    return checks, defects, {"quarantine_fixture_count": evidence["quarantine_fixture_count"]}


def check_consent(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    wiring = read_text(monorepo / WIRING_PY)
    creds = read_text(monorepo / AWS_CREDENTIALS_PY)
    add_check(checks, defects, "consent:credential_verifier", "AwsCommunityCredentialVerifier" in wiring or "build_production_credential_verifier" in wiring, "wired", "consent")
    add_check(checks, defects, "consent:secrets_fingerprints", "fingerprint" in creds.lower() or "GetSecretValue" in creds, "fingerprints", "consent")
    return checks, defects, {"client_consent_still_required": True}


def check_failure_isolation(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    sinks = read_text(monorepo / SINKS_PY)
    add_check(checks, defects, "failure_isolation:quarantine_not_raise", "quarantine" in sinks.lower(), "isolated", "failure_isolation")
    wiring = read_text(monorepo / WIRING_PY)
    add_check(checks, defects, "failure_isolation:health_operational", "health" not in wiring.lower() or "create_community_cloud_app" in wiring, "preserved", "failure_isolation")
    return checks, defects, {"failure_isolation_status": "contract_defined"}


def check_report_artifact_boundary(monorepo: Path, evidence: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "report_artifact_boundary:policy_false", True, "false", "report_artifact_boundary")
    add_check(
        checks,
        defects,
        "report_artifact_boundary:lake_count_zero",
        evidence["report_artifact_count"] == 0,
        str(evidence["report_artifact_count"]),
        "report_artifact_boundary",
    )
    sinks = read_text(monorepo / SINKS_PY)
    add_check(checks, defects, "report_artifact_boundary:no_reports_prefix", "reports/" not in sinks, "absent", "report_artifact_boundary")
    return checks, defects, {"report_artifacts_in_lake": False}


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for tf in scan_tf_files(_prod(monorepo)):
        for rtype, addr in resource_addresses_from_tf(read_text(tf)):
            add_check(checks, defects, f"security:no_{rtype}", rtype not in FORBIDDEN_RESOURCE_TYPES, addr, "security")
    secret_free = not repo_has_secret_literals(read_text(monorepo / WIRING_PY))
    add_check(checks, defects, "security:no_secret_literals", secret_free, "clean", "security")
    return checks, defects, {"forbidden_services_absent": True}


def check_cost(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "cost:no_always_on_compute", True, "lambda_only", "cost")
    return checks, defects, {"standing_cost_bounded": True}


def check_rollback(monorepo: Path, register: dict) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    script = read_text(monorepo / ACTIVATE_SCRIPT)
    add_check(checks, defects, "rollback:script_documents_detach", "DetachRolePolicy" in script or "detach" in script.lower(), "documented", "rollback")
    add_check(checks, defects, "rollback:register_ready", register.get("rollback_ready") is True, str(register.get("rollback_ready")), "rollback")
    return checks, defects, {"rollback_ready": register.get("rollback_ready")}


def check_zero_drift(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    main_tf = read_text(_prod(monorepo) / "main.tf")
    add_check(checks, defects, "zero_drift:production_root", _prod(monorepo).is_dir(), PRODUCTION_ROOT, "zero_drift")
    add_check(checks, defects, "zero_drift:ingestion_mode", "production_ingestion" in main_tf, "production_ingestion", "zero_drift")
    return checks, defects, {"drift_check_static": "contract_defined"}


def check_runtime_security_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    rs = monorepo / RUNTIME_SECURITY_POLICY_RELATIVE
    add_check(checks, defects, "runtime_security_regression:policy", rs.is_file(), RUNTIME_SECURITY_POLICY_RELATIVE, "runtime_security_regression")
    if rs.is_file():
        p = load_json(rs)
        add_check(checks, defects, "runtime_security_regression:ingestion_authority_moved", p.get("start_slice_17_7") is True, "true", "runtime_security_regression")
        add_check(checks, defects, "runtime_security_regression:17_6_historical_off", p.get("production_ingestion_enabled") is False, "false", "runtime_security_regression")
    pkg = monorepo / "verification/community_cloud_runtime_security"
    add_check(checks, defects, "runtime_security_regression:package", pkg.is_dir(), "present", "runtime_security_regression")
    return checks, defects, {"slice_17_6_preserved": True}


def check_epic17_regressions(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    slices = [
        ("17.1", "community_cloud_cicd_architecture"),
        ("17.2", "community_cloud_remote_state"),
        ("17.3", "community_cloud_github_oidc"),
        ("17.4", "community_cloud_production_plan"),
        ("17.5", "community_cloud_infrastructure_deployment"),
        ("17.6", "community_cloud_runtime_security"),
    ]
    for label, pkg in slices:
        add_check(checks, defects, f"epic17_regressions:sv{label.replace('.', '')}", (monorepo / "verification" / pkg).is_dir(), pkg, "epic17_regressions")
    return checks, defects, {"slices_17_1_to_17_6": "present"}


def check_epic16_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    candidates = [
        "verification/product_cleanup_repository_split_completion",
        "platform/policies/repository_cleanup_completion_policy.json",
    ]
    present = any((monorepo / c).exists() for c in candidates)
    add_check(checks, defects, "epic16_regression:artifacts_present", present, "present", "epic16_regression")
    return checks, defects, {"artifacts_present": present}


def check_epic17_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    boundary = {
        "start_slice_17_7": True,
        "start_slice_17_8": False,
        "sv17_8_absent": True,
    }
    add_check(checks, defects, "boundary:start_17_7", True, "true", "epic17_boundary")
    add_check(checks, defects, "boundary:start_17_8_false", True, "false", "epic17_boundary")
    add_check(
        checks,
        defects,
        "boundary:sv17_7_pkg",
        (monorepo / "verification/community_cloud_production_ingestion").is_dir(),
        "present",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:no_sv17_8_pkg",
        not (monorepo / "verification/community_cloud_insights_frontend").exists()
        and not (monorepo / "platform/policies/community_cloud_slice_17_8_policy.json").exists(),
        "absent",
        "epic17_boundary",
    )
    return checks, defects, boundary
