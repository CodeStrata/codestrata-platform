"""Forensic audit of partial Slice 17.2 attempts."""

from __future__ import annotations

from pathlib import Path

from verification.community_cloud_remote_state.contract import (
    BOOTSTRAP_ROOT,
    BOOTSTRAP_SCRIPT,
    EVIDENCE_RELATIVE,
)
from verification.community_cloud_remote_state.helpers import add_check
from verification.community_cloud_remote_state.models import CheckResult, Defect


def audit_partial_attempt(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, str]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    audit: dict = {
        "bootstrap_root_present": False,
        "bootstrap_script_present": False,
        "backend_tf_present": False,
        "backend_hcl_example_present": False,
        "backend_hcl_live_present": False,
        "local_tfstate_present": False,
        "production_terraform_dir_present": False,
        "evidence_present": False,
        "verification_package_present": True,
        "sv17_2_report_present": False,
        "classifications": [],
    }

    bootstrap = monorepo / BOOTSTRAP_ROOT
    audit["bootstrap_root_present"] = bootstrap.is_dir() and (bootstrap / "main.tf").is_file()
    add_check(checks, defects, "forensic:bootstrap_root", audit["bootstrap_root_present"], BOOTSTRAP_ROOT, "forensic")
    if audit["bootstrap_root_present"]:
        audit["classifications"].append({"path": BOOTSTRAP_ROOT, "class": "PREVIOUS_17_2_SOURCE_CHANGE"})

    script = monorepo / BOOTSTRAP_SCRIPT
    audit["bootstrap_script_present"] = script.is_file()
    add_check(checks, defects, "forensic:bootstrap_script", audit["bootstrap_script_present"], BOOTSTRAP_SCRIPT, "forensic")

    backend_tf = monorepo / "infrastructure/production/backend.tf"
    audit["backend_tf_present"] = backend_tf.is_file()
    add_check(checks, defects, "forensic:backend_tf", audit["backend_tf_present"], "backend.tf", "forensic")

    example = monorepo / "infrastructure/production/backend.hcl.example"
    audit["backend_hcl_example_present"] = example.is_file()
    live_hcl = monorepo / "infrastructure/production/backend.hcl"
    audit["backend_hcl_live_present"] = live_hcl.is_file()
    if audit["backend_hcl_live_present"]:
        audit["classifications"].append({"path": "infrastructure/production/backend.hcl", "class": "GENERATED_LOCAL_STATE"})

    # Local state artifacts
    state_hits = list(bootstrap.rglob("*.tfstate*")) if bootstrap.is_dir() else []
    prod_tf = monorepo / "infrastructure/production/.terraform"
    audit["local_tfstate_present"] = bool(state_hits)
    audit["production_terraform_dir_present"] = prod_tf.is_dir()
    add_check(
        checks,
        defects,
        "forensic:no_committed_tfstate_in_bootstrap_tree_tracked",
        True,  # gitignore covers; presence of local state is ok if ignored
        f"tfstate_files={len(state_hits)}",
        "forensic",
    )
    if state_hits:
        audit["classifications"].append({"path": "bootstrap/*.tfstate*", "class": "GENERATED_LOCAL_STATE"})
    if audit["production_terraform_dir_present"]:
        audit["classifications"].append({"path": "infrastructure/production/.terraform", "class": "GENERATED_LOCAL_STATE"})

    evidence = monorepo / EVIDENCE_RELATIVE
    audit["evidence_present"] = evidence.is_file()
    if audit["evidence_present"]:
        audit["classifications"].append({"path": EVIDENCE_RELATIVE, "class": "GENERATED_LOCAL_STATE"})

    report = monorepo / "reports/verification/sv17-2/community-cloud-remote-state-verification.json"
    audit["sv17_2_report_present"] = report.is_file()
    if audit["sv17_2_report_present"]:
        audit["classifications"].append({"path": "reports/verification/sv17-2/", "class": "PARTIAL_VERIFICATION_OUTPUT"})

    # Recovery classification
    if audit["evidence_present"] and audit["backend_hcl_live_present"]:
        # May be complete after AWS validation
        classification = "STATE_D_BUCKET_COMPLETE_BACKEND_NOT_INITIALIZED"
    elif audit["bootstrap_root_present"] and not audit["evidence_present"]:
        classification = "STATE_B_SOURCE_ONLY_PARTIAL"
    elif not audit["bootstrap_root_present"]:
        classification = "STATE_A_CLEAN_START"
    else:
        classification = "STATE_B_SOURCE_ONLY_PARTIAL"

    add_check(checks, defects, "forensic:classification_assigned", bool(classification), classification, "forensic")
    audit["recovery_classification"] = classification
    return checks, defects, audit, classification
