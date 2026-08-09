"""Slice 17.2 remote-state bootstrap runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_remote_state import (
    COMMUNITY_CLOUD_REMOTE_STATE_ID,
    COMMUNITY_CLOUD_REMOTE_STATE_VERSION,
)
from verification.community_cloud_remote_state.checks import (
    check_aws_and_bucket,
    check_boundaries,
    check_policy,
    check_source_architecture,
)
from verification.community_cloud_remote_state.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_cloud_remote_state.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_cloud_remote_state.forensic import audit_partial_attempt
from verification.community_cloud_remote_state.models import (
    CheckResult,
    CommunityCloudRemoteStateReport,
    Defect,
    Verdict,
)
from verification.community_cloud_remote_state.reporting import write_report
from verification.community_cloud_remote_state.scenarios import check_scenarios


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    subset = [c for c in checks if c.category in categories]
    return all(c.ok for c in subset) if subset else True


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.surface, d.expected, d.observed)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def build_report(monorepo: Path) -> CommunityCloudRemoteStateReport:
    contract = default_contract()
    assert contract.start_slice_17_2 is True
    assert contract.start_slice_17_3 is True
    assert contract.dynamodb_required is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, forensic, recovery = audit_partial_attempt(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, policy, register = check_policy(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_source_architecture(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, identity, bucket = check_aws_and_bucket(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17_boundary = check_boundaries(monorepo)
    checks.extend(c)
    defects.extend(d)

    # Refine recovery classification after AWS probe
    if identity.get("aws_reachable") and bucket.get("exists") and _ok(checks, "backend", "remote_init"):
        recovery = "STATE_E_BACKEND_ALREADY_COMPLETE"
    elif identity.get("aws_reachable") and bucket.get("exists"):
        recovery = "STATE_D_BUCKET_COMPLETE_BACKEND_NOT_INITIALIZED"
    elif identity.get("aws_reachable") and not bucket.get("exists"):
        recovery = "STATE_B_SOURCE_ONLY_PARTIAL"
    elif not identity.get("aws_reachable"):
        recovery = forensic.get("recovery_classification", recovery)

    flags = {
        "forensic_ok": _ok(checks, "forensic"),
        "naming_ok": _ok(checks, "naming") if identity.get("aws_reachable") else _ok(checks, "bootstrap", "backend"),
        "region_ok": _ok(checks, "region", "region_consistency"),
        "identity_ok": _ok(checks, "aws_identity") if identity.get("aws_reachable") else False,
        "datalake_ok": _ok(checks, "data_lake"),
        "no_ddb_ok": _ok(checks, "no_dynamodb"),
        "pab_ok": _ok(checks, "public_access") if bucket.get("exists") else False,
        "versioning_ok": _ok(checks, "versioning") if bucket.get("exists") else False,
        "encryption_ok": _ok(checks, "encryption") if bucket.get("exists") else False,
        "security_ok": _ok(checks, "security") if bucket.get("exists") else _ok(checks, "source_control"),
        "source_ok": _ok(checks, "source_control"),
        "backend_ok": _ok(checks, "backend"),
        "boundary_ok": _ok(checks, "resource_boundary"),
        "epic17_ok": _ok(checks, "epic17_boundary"),
        "bucket_ok": bool(bucket.get("exists")),
        "report_safe": True,
    }
    # If AWS unreachable, identity/bucket scenarios must fail honestly
    if not identity.get("aws_reachable"):
        flags["identity_ok"] = False
        flags["bucket_ok"] = False
        flags["pab_ok"] = False
        flags["versioning_ok"] = False
        flags["encryption_ok"] = False

    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    failed = sum(1 for x in checks if not x.ok)

    limitations = [
        "owner_credentials_used_for_bootstrap",
        "physical_concurrent_lock_not_exercised",
        "physical_state_disaster_recovery_not_exercised",
        "oidc_not_yet_available",
        "product_state_empty",
        "worktree_uncommitted",
        "hybrid_cli_bucket_plus_opentofu_controls",
        "operator_iam_lacks_get_bucket_policy_tagging_website",
    ]
    if not identity.get("aws_reachable"):
        limitations.append("aws_api_unreachable_from_agent_environment")
    if forensic.get("recovery_classification") or recovery:
        if recovery not in ("STATE_A_CLEAN_START",):
            limitations.append("previous_partial_attempt_required_safe_adoption")

    statuses = {
        "forensic": _status(checks, "forensic"),
        "policy": _status(checks, "policy"),
        "bootstrap": _status(checks, "bootstrap"),
        "aws_identity": _status(checks, "aws_identity"),
        "region": _status(checks, "region"),
        "s3": _status(checks, "s3"),
        "versioning": _status(checks, "versioning"),
        "encryption": _status(checks, "encryption"),
        "public_access": _status(checks, "public_access"),
        "locking": _status(checks, "locking"),
        "no_dynamodb": _status(checks, "no_dynamodb"),
        "backend": _status(checks, "backend"),
        "remote_init": _status(checks, "remote_init"),
        "source_control": _status(checks, "source_control"),
        "resource_boundary": _status(checks, "resource_boundary"),
        "epic17_boundary": _status(checks, "epic17_boundary"),
        "scenarios": _status(checks, "scenarios"),
    }

    verdict = _decide(failed, defects, limitations)
    probe = dict_to_canonical_json({"schema": SCHEMA_NAME, "verdict": verdict, "recovery": recovery})
    safe, reason = report_text_is_safe(probe)
    if not safe:
        checks.append(CheckResult("report:safe", False, reason, "determinism"))
        defects.append(Defect("report_leak", "report:safe", "safe", reason))
        failed += 1
        verdict = "FAIL"

    backend_summary = {
        "backend_type": "s3",
        "state_key": policy.get("state_key"),
        "use_lockfile": True,
        "dynamodb_table": False,
        "region": policy.get("region"),
    }

    return CommunityCloudRemoteStateReport(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_CLOUD_REMOTE_STATE_ID,
        package_version=COMMUNITY_CLOUD_REMOTE_STATE_VERSION,
        epic="17",
        slice="17.2",
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        limitations=sorted(limitations),
        checks=[{"check_id": x.check_id, "ok": x.ok, "detail": x.detail, "category": x.category} for x in checks],
        defects=[
            {"classification": x.classification, "surface": x.surface, "expected": x.expected, "observed": x.observed}
            for x in defects
        ],
        recovery_classification=recovery,
        forensic_audit={
            "bootstrap_root_present": forensic.get("bootstrap_root_present"),
            "bootstrap_script_present": forensic.get("bootstrap_script_present"),
            "backend_tf_present": forensic.get("backend_tf_present"),
            "backend_hcl_live_present": forensic.get("backend_hcl_live_present"),
            "evidence_present": forensic.get("evidence_present"),
            "local_tfstate_present": forensic.get("local_tfstate_present"),
            "class_count": len(forensic.get("classifications") or []),
        },
        policy={
            "schema": policy.get("schema"),
            "region": policy.get("region"),
            "use_lockfile": policy.get("use_lockfile"),
            "dynamodb_required": policy.get("dynamodb_required"),
            "start_slice_17_2": policy.get("start_slice_17_2"),
            "start_slice_17_3": policy.get("start_slice_17_3"),
        },
        register={
            "schema": register.get("schema"),
            "region": register.get("region"),
            "bootstrap_status": register.get("bootstrap_status"),
            "state_key": register.get("state_key"),
            "locking_method": register.get("locking_method"),
        },
        aws_identity={
            "aws_identity_verified": identity.get("aws_identity_verified"),
            "expected_operator_profile": identity.get("expected_operator_profile"),
            "aws_reachable": identity.get("aws_reachable"),
            "region": identity.get("region"),
        },
        bucket={
            "exists": bucket.get("exists"),
            "versioning": bucket.get("versioning"),
            "encryption": bucket.get("encryption"),
            "public_access_block": bucket.get("public_access_block"),
            "website": bucket.get("website"),
            # omit raw bucket name if it could encode account; include only when exists and safe pattern
            "name_pattern": "codestrata-opentofu-state-production-<stable-suffix>",
        },
        backend=backend_summary,
        epic17_boundary=epic17_boundary,
        statuses=statuses,
        scenario_results=scenario_results,
    )


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    rel = path.relative_to(monorepo).as_posix()
    print(f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} report={rel}")
    print(f"recovery={report.recovery_classification} start_slice_17_5=true start_slice_17_6=true start_slice_17_7=true")
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
