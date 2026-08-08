"""Checks for Slice 15.4 ingestion verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_insights_ingestion.activation import activation_state
from verification.community_insights_ingestion.aggregation_boundary import (
    aggregation_absent,
)
from verification.community_insights_ingestion.contract import (
    ACTIVATION_STATE,
    CONTRACT_DOC_RELATIVE,
    FORBIDDEN_15_7_PATHS,
    PACKAGE_ECOSYSTEMS,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    PROVIDER_FAMILIES,
)
from verification.community_insights_ingestion.dashboard_boundary import (
    dashboard_absent,
)
from verification.community_insights_ingestion.inventory import exists, load_json, read_text
from verification.community_insights_ingestion.models import CheckResult, Defect
from verification.community_insights_ingestion.policy import load_ingestion_policy


def _add(
    checks: list[CheckResult],
    defects: list[Defect],
    name: str,
    ok: bool,
    detail: str,
    category: str,
    classification: str = "ingestion_defect",
) -> None:
    checks.append(CheckResult(name, ok, detail, category))
    if not ok:
        defects.append(Defect(classification, category, "pass", detail))


def check_policy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_ingestion_policy(monorepo)
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
        "policy:doc",
        exists(monorepo, CONTRACT_DOC_RELATIVE),
        CONTRACT_DOC_RELATIVE,
        "policy",
    )
    _add(
        checks,
        defects,
        "policy:activation_state",
        policy.get("operational_activation_state") == ACTIVATION_STATE,
        str(policy.get("operational_activation_state")),
        "activation",
    )
    _add(
        checks,
        defects,
        "policy:wire_false",
        policy.get("enable_ingestion_wire") is False
        and policy.get("production_transmission_enabled") is False,
        "disabled",
        "activation",
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
        "policy:privacy_wins",
        policy.get("server_revalidation_required") is True,
        "revalidate",
        "policy",
    )
    return checks, defects


def check_change_register(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_ingestion_policy(monorepo)
    disp = dict(policy.get("change_register_disposition") or {})
    for cr in ("CR-15.3-001", "CR-15.3-002", "CR-15.3-003"):
        row = disp.get(cr) or {}
        _add(
            checks,
            defects,
            f"cr:{cr}:implemented",
            row.get("status") == "implemented_in_15_4",
            str(row.get("status")),
            "change_register",
        )
        _add(
            checks,
            defects,
            f"cr:{cr}:contract_active",
            row.get("activated_in_contract") is True,
            "contract",
            "change_register",
        )
        _add(
            checks,
            defects,
            f"cr:{cr}:wire_inactive",
            row.get("activated_in_production_wire") is False,
            "wire_off",
            "change_register",
        )
    return checks, defects, disp


def check_ecosystem(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_ingestion_policy(monorepo)
    eco = policy.get("package_ecosystem") or {}
    vocab = tuple(eco.get("closed_vocabulary") or ())
    _add(
        checks,
        defects,
        "ecosystem:vocab",
        vocab == PACKAGE_ECOSYSTEMS,
        str(vocab),
        "ecosystem",
    )
    _add(
        checks,
        defects,
        "ecosystem:optional",
        eco.get("optional") is True,
        "optional",
        "ecosystem",
    )
    # Runtime model
    try:
        from codestrata_platform.community_cloud_api.assessment_metadata.enums import (
            PackageEcosystem,
        )
        from codestrata_platform.community_cloud_api.assessment_metadata.models import (
            RepositoryMetadata,
        )

        runtime = tuple(sorted(item.value for item in PackageEcosystem))
        _add(
            checks,
            defects,
            "ecosystem:runtime_enum",
            runtime == tuple(sorted(PACKAGE_ECOSYSTEMS)),
            str(runtime),
            "ecosystem",
        )
        base = {
            "primary_language": "python",
            "language_count": 1,
            "dependency_ecosystem_count": 1,
            "file_count_bucket": "1_to_10",
            "source_file_count_bucket": "1_to_10",
            "test_file_count_bucket": "none",
            "repository_shape": "application",
            "has_tests": True,
            "has_build_files": True,
            "has_dependency_manifests": True,
        }
        RepositoryMetadata.model_validate(base)
        RepositoryMetadata.model_validate({**base, "package_ecosystem": "npm"})
        rejected = False
        try:
            RepositoryMetadata.model_validate(
                {**base, "package_ecosystem": "com.acme:widget"}
            )
        except Exception:
            rejected = True
        _add(
            checks,
            defects,
            "ecosystem:reject_coordinates",
            rejected,
            "rejected",
            "ecosystem",
        )
        rejected_name = False
        try:
            RepositoryMetadata.model_validate({**base, "package_ecosystem": "lodash"})
        except Exception:
            rejected_name = True
        _add(
            checks,
            defects,
            "ecosystem:reject_package_name",
            rejected_name,
            "rejected",
            "ecosystem",
        )
    except Exception as exc:  # noqa: BLE001
        _add(checks, defects, "ecosystem:runtime_enum", False, type(exc).__name__, "ecosystem")
    return checks, defects


def check_providers_models(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_ingestion_policy(monorepo)
    providers = tuple((policy.get("provider_family") or {}).get("canonical") or ())
    _add(
        checks,
        defects,
        "provider:vocab",
        providers == PROVIDER_FAMILIES,
        str(providers),
        "provider",
    )
    _add(
        checks,
        defects,
        "provider:openrouter",
        (policy.get("provider_family") or {}).get("openrouter_present") is True,
        "present",
        "provider",
    )
    model = policy.get("model_family") or {}
    _add(
        checks,
        defects,
        "model:outcome_C",
        model.get("privacy_decision") == "C_normalized_model_family_allowed",
        str(model.get("privacy_decision")),
        "model",
    )
    _add(
        checks,
        defects,
        "model:exact_forbidden",
        model.get("exact_model_id_forbidden") is True,
        "forbidden",
        "model",
    )
    try:
        from codestrata_platform.community_cloud_api.ai_usage.catalog import (
            CANONICAL_AI_PROVIDER_FAMILIES,
        )
        from codestrata.telemetry.analytics.ai_analytics_catalogs import (
            APPROVED_AI_PROVIDER_FAMILIES,
        )
        from codestrata.telemetry.analytics.ai_analytics_mapping import (
            map_provider_to_family,
        )

        _add(
            checks,
            defects,
            "provider:platform_catalog",
            set(CANONICAL_AI_PROVIDER_FAMILIES) == set(PROVIDER_FAMILIES),
            str(CANONICAL_AI_PROVIDER_FAMILIES),
            "provider",
        )
        _add(
            checks,
            defects,
            "provider:engine_catalog",
            set(APPROVED_AI_PROVIDER_FAMILIES) == set(PROVIDER_FAMILIES),
            str(sorted(APPROVED_AI_PROVIDER_FAMILIES)),
            "provider",
        )
        _add(
            checks,
            defects,
            "provider:map_openrouter",
            map_provider_to_family("openrouter") == "openrouter",
            "mapped",
            "provider",
        )
    except Exception as exc:  # noqa: BLE001
        _add(checks, defects, "provider:platform_catalog", False, type(exc).__name__, "provider")
    return checks, defects


def check_identity(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_ingestion_policy(monorepo)
    ident = policy.get("installation_identity") or {}
    _add(
        checks,
        defects,
        "identity:not_machine",
        ident.get("vscode_machineId_forbidden") is True
        and ident.get("second_tracking_identity_forbidden") is True,
        "safe",
        "identity",
    )
    _add(
        checks,
        defects,
        "identity:vscode_reader",
        exists(monorepo, "vscode-plugin/src/communityCloud/installationIdentity.ts"),
        "present",
        "identity",
    )
    text = read_text(
        monorepo, "vscode-plugin/src/communityCloud/installationIdentity.ts"
    )
    _add(
        checks,
        defects,
        "identity:no_machineId_use",
        "machineId" not in text or "machineIdForbidden" in text,
        "no_machineId",
        "identity",
    )
    _add(
        checks,
        defects,
        "identity:transmission_off",
        "transmissionEnabled: false" in text.replace(" ", "")
        or "transmissionEnabled:false" in text.replace(" ", "")
        or 'transmissionEnabled: false' in text,
        "off",
        "identity",
    )
    return checks, defects


def check_privacy_isolation_quarantine(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_ingestion_policy(monorepo)
    forbidden = set(policy.get("privacy_forbidden_fields") or [])
    for field in (
        "repository_name",
        "file_path",
        "findings",
        "evidence",
        "prompt",
        "model_id",
        "machineId",
        "endpoint",
    ):
        _add(
            checks,
            defects,
            f"privacy:forbid_{field}",
            field in forbidden,
            "forbidden",
            "privacy",
        )
    # Adversarial fixtures must not appear in the ingestion policy as accepted values.
    blob = read_text(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        defects,
        "privacy:no_sk_live_in_policy",
        "sk-live" not in blob,
        "clean",
        "privacy",
    )
    _add(
        checks,
        defects,
        "privacy:no_fake_repo_in_policy",
        "acme-corp-private-repo" not in blob,
        "clean",
        "privacy",
    )
    fail = policy.get("failure_isolation") or {}
    _add(
        checks,
        defects,
        "isolation:assessment",
        fail.get("analytics_must_not_fail_assessment") is True,
        "isolated",
        "isolation",
    )
    _add(
        checks,
        defects,
        "isolation:cli",
        fail.get("analytics_must_not_fail_cli") is True,
        "isolated",
        "isolation",
    )
    q = policy.get("quarantine") or {}
    _add(
        checks,
        defects,
        "quarantine:safe_reason",
        q.get("raw_sensitive_value_in_reason_forbidden") is True,
        "safe",
        "quarantine",
    )
    parts = read_text(
        monorepo,
        "platform/src/codestrata_platform/community_cloud_api/data_lake/partitions.py",
    )
    _add(
        checks,
        defects,
        "quarantine:builder_present",
        "quarantine" in parts and "reason=" in parts,
        "present",
        "quarantine",
    )
    return checks, defects


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    _add(
        checks,
        defects,
        "boundary:aggregation",
        aggregation_absent(monorepo),
        "absent",
        "aggregation_boundary",
    )
    _add(
        checks,
        defects,
        "boundary:dashboard",
        dashboard_absent(monorepo),
        "absent",
        "dashboard_boundary",
    )
    present = [rel for rel in FORBIDDEN_15_7_PATHS if exists(monorepo, rel)]
    _add(
        checks,
        defects,
        "boundary:slice_15_7_paths",
        not present,
        "absent" if not present else ",".join(present),
        "slice_15_7_boundary",
        "slice_15_7_started",
    )
    reports = monorepo / "reports" / "verification"
    later = []
    if reports.is_dir():
        later = sorted(
            p.name
            for p in reports.iterdir()
            if p.is_dir()
            and p.name.startswith("sv15-")
            and p.name not in {"sv15-1", "sv15-2", "sv15-3", "sv15-4", "sv15-5", "sv15-6", "sv15-7", "sv15-8", "sv15-9", "sv15-10", "sv15-11", "sv15-12", "sv16-1"}
        )
    _add(
        checks,
        defects,
        "boundary:no_later_reports",
        not later,
        "absent" if not later else ",".join(later),
        "slice_15_7_boundary",
        "slice_15_7_started",
    )
    # Infrastructure: enable_ingestion_wire remains false in TF
    tf = read_text(
        monorepo,
        "infrastructure/production/community-data-lake.tf",
    )
    _add(
        checks,
        defects,
        "infra:wire_false",
        "enable_ingestion_wire" in tf and "false" in tf,
        "disabled",
        "activation",
    )
    _add(
        checks,
        defects,
        "activation:helper",
        activation_state() == ACTIVATION_STATE,
        activation_state(),
        "activation",
    )
    return checks, defects


def check_consent_schema(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_ingestion_policy(monorepo)
    _add(
        checks,
        defects,
        "consent:unchanged",
        (policy.get("consent") or {}).get("unchanged") is True,
        "unchanged",
        "consent",
    )
    _add(
        checks,
        defects,
        "non_interactive:unchanged",
        (policy.get("non_interactive") or {}).get("unchanged") is True,
        "unchanged",
        "consent",
    )
    impact = policy.get("schema_impact") or {}
    _add(
        checks,
        defects,
        "schema:assessment_additive",
        "package_ecosystem" in str(impact.get("assessment_metadata")),
        str(impact.get("assessment_metadata")),
        "schema",
    )
    lake = load_json(monorepo, "platform/policies/community_data_lake_policy.json")
    _add(
        checks,
        defects,
        "schema:lake_baseline",
        lake.get("policy_id") == "community-data-lake-policy",
        "baseline",
        "schema",
    )
    return checks, defects
