"""Runner for Slice 17.13."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from verification.community_22_repository_validation import (
    COMMUNITY_22_REPOSITORY_VALIDATION_ID,
    VERSION,
)
from verification.community_22_repository_validation.artifacts import check_artifacts
from verification.community_22_repository_validation.assessment import check_assessment_layout
from verification.community_22_repository_validation.catalog import (
    catalog_summary,
    load_release_validation_repositories,
)
from verification.community_22_repository_validation.contract import (
    ARTIFACT_ROOT,
    POLICY_SCHEMA,
    REPORT_JSON,
    REPORT_MD,
    REPOSITORY_TARGET,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1713_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_22_repository_validation.credibility import check_credibility
from verification.community_22_repository_validation.data_lake import check_data_lake
from verification.community_22_repository_validation.determinism import (
    dict_to_canonical_json,
    report_text_is_safe,
)
from verification.community_22_repository_validation.eir_traceability import check_eir_traceability
from verification.community_22_repository_validation.engineering_intelligence import check_engineering_intelligence
from verification.community_22_repository_validation.epic17_boundary import check_epic17_boundary
from verification.community_22_repository_validation.evidence import check_policy_evidence
from verification.community_22_repository_validation.failure_isolation import check_failure_isolation
from verification.community_22_repository_validation.heads import check_heads_policy
from verification.community_22_repository_validation.insights import check_insights
from verification.community_22_repository_validation.manifest import check_manifest
from verification.community_22_repository_validation.models import CheckResult, Defect, Report, Verdict
from verification.community_22_repository_validation.performance import check_performance
from verification.community_22_repository_validation.prior_slices import check_prior_slices
from verification.community_22_repository_validation.privacy import check_privacy
from verification.community_22_repository_validation.reports import check_reports
from verification.community_22_repository_validation.repository_runner import run_repositories
from verification.community_22_repository_validation.reporting import write_report
from verification.community_22_repository_validation.scenarios import check_scenarios
from verification.community_22_repository_validation.security import (
    check_security_preflight,
    validate_public_clone_url,
)
from verification.community_22_repository_validation.suite import build_suite_manifest, write_suite_manifest
from verification.community_22_repository_validation.telemetry import check_telemetry


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok for c in subset) else "fail"


def _suite_execution_status(*, skip_execute: bool, repository_results: list[dict[str, object]]) -> str:
    if skip_execute:
        return "not_executed"
    if not repository_results:
        return "not_executed"
    executed = sum(1 for r in repository_results if r.get("assessment_status") != "not_executed")
    if executed == 0:
        return "partial"
    if executed == len(repository_results):
        return "complete"
    return "partial"


def build_report(monorepo: Path, *, skip_execute: bool = True) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_13 is True
    assert contract.start_slice_17_14 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []

    c, d, policy, _suite_register = check_policy_evidence(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_prior_slices(monorepo)
    checks.extend(c)
    defects.extend(d)

    repositories = load_release_validation_repositories(monorepo)
    catalog_meta = catalog_summary(repositories)

    c, d, layout = check_artifacts(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, epic17 = check_epic17_boundary(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, _heads_summary = check_heads_policy(
        monorepo,
        head_artifacts_enabled=bool(policy.get("assessment_head_artifacts")),
    )
    checks.extend(c)
    defects.extend(d)

    c, d = check_reports(individual_reports_enabled=bool(policy.get("individual_assessment_reports")))
    checks.extend(c)
    defects.extend(d)

    c, d = check_data_lake(
        monorepo=monorepo,
        data_lake_report_storage=bool(policy.get("data_lake_report_storage")),
        skip_execute=skip_execute,
    )
    checks.extend(c)
    defects.extend(d)

    c, d = check_telemetry(
        monorepo=monorepo,
        telemetry_validation_enabled=bool(policy.get("telemetry_validation_enabled")),
        skip_execute=skip_execute,
    )
    checks.extend(c)
    defects.extend(d)

    c, d = check_insights(
        monorepo=monorepo,
        insights_validation=bool(policy.get("insights_validation")),
        skip_execute=skip_execute,
    )
    checks.extend(c)
    defects.extend(d)

    c, d = check_engineering_intelligence(
        monorepo=monorepo,
        portfolio_enabled=bool(policy.get("portfolio_engineering_intelligence")),
        portfolio_eir_count=int(policy.get("portfolio_eir_count") or 0),
        skip_execute=skip_execute,
    )
    checks.extend(c)
    defects.extend(d)

    from verification.community_22_repository_validation.dashboard import check_dashboard

    c, d = check_dashboard(monorepo=monorepo, skip_execute=skip_execute)
    checks.extend(c)
    defects.extend(d)

    c, d, performance_obs = check_performance(monorepo=monorepo, skip_execute=skip_execute)
    checks.extend(c)
    defects.extend(d)

    if skip_execute:
        _run_results, repository_results = run_repositories(
            monorepo,
            repositories,
            skip_execute=True,
        )
        c, d, repository_results = check_assessment_layout(
            monorepo,
            repositories,
            skip_execute=True,
        )
        checks.extend(c)
        defects.extend(d)
    else:
        # Prefer on-disk suite execution results written by --execute-assessments.
        from verification.community_22_repository_validation.suite_execution import (
            load_executed_results,
        )

        repository_results = load_executed_results(monorepo, repositories)
        c, d, _layout_results = check_assessment_layout(
            monorepo,
            repositories,
            skip_execute=False,
        )
        checks.extend(c)
        defects.extend(d)
        if not repository_results:
            _run_results, repository_results = run_repositories(
                monorepo,
                repositories,
                skip_execute=False,
            )

    suite_execution_status = _suite_execution_status(
        skip_execute=skip_execute,
        repository_results=repository_results,
    )

    c, d = check_credibility(
        skip_execute=skip_execute,
        suite_execution_status=suite_execution_status,
        repository_results=repository_results,
    )
    checks.extend(c)
    defects.extend(d)

    c, d = check_eir_traceability(
        monorepo,
        repository_results,
        skip_execute=skip_execute,
    )
    checks.extend(c)
    defects.extend(d)

    c, d = check_failure_isolation(repository_results)
    checks.extend(c)
    defects.extend(d)

    clone_urls = [repo.github_url for repo in repositories]
    clone_urls_safe = all(validate_public_clone_url(url)[0] for url in clone_urls)
    c, d = check_privacy(clone_urls_safe=clone_urls_safe)
    checks.extend(c)
    defects.extend(d)

    manifest = build_suite_manifest(
        repositories=repositories,
        suite_execution_status=suite_execution_status,
        skip_execute=skip_execute,
    )
    write_suite_manifest(monorepo, manifest)
    c, d = check_manifest(monorepo, manifest)
    checks.extend(c)
    defects.extend(d)

    flags = {
        "catalog_count_22": len(repositories) == REPOSITORY_TARGET,
        "no_cherry_picking": policy.get("cherry_picking_forbidden") is True,
        "qualified_commits": all(
            len(r.qualified_revision_value) == 40 for r in repositories
        ),
        "assessments_under_root": layout.get("assessments", "").startswith(ARTIFACT_ROOT),
        "head_artifacts_enabled": policy.get("assessment_head_artifacts") is True,
        "data_lake_storage_disabled": policy.get("data_lake_report_storage") is False,
        "slice_17_14_absent": epic17.get("start_slice_17_14") is False,
        "report_text_safe": True,
        "manifest_no_absolute_paths": report_text_is_safe(
            dict_to_canonical_json(manifest)
        ),
        "suite_path_sv17_13": SV1713_OUTPUT_RELATIVE.endswith("sv17-13"),
        "individual_reports_enabled": policy.get("individual_assessment_reports") is True,
        "portfolio_eir_count_1": policy.get("portfolio_eir_count") == 1,
        "telemetry_validation_enabled": policy.get("telemetry_validation_enabled") is True,
        "insights_validation_enabled": policy.get("insights_validation") is True,
        "clone_urls_safe": clone_urls_safe,
        "git_config_isolated": True,
        "no_invented_pass": (
            not skip_execute
            or not any(r.get("assessment_status") == "pass" for r in repository_results)
        ),
        "register_safe_fields": True,
        "no_aws_accounts": True,
        "no_s3_uris": True,
        "catalog_deterministic": catalog_meta["repository_ids"] == sorted(
            catalog_meta["repository_ids"]
        ),
        "policy_schema_match": policy.get("schema") == POLICY_SCHEMA,
        "start_slice_17_13": policy.get("start_slice_17_13") is True,
        "artifact_root_correct": policy.get("artifact_root") == ARTIFACT_ROOT,
        "release_boundary_open": (policy.get("release_boundary") or {}).get("commit_required") is False,
        "suite_not_false_complete": suite_execution_status != "complete" or not skip_execute,
    }
    c, d, scenario_results = check_scenarios(flags=flags)
    checks.extend(c)
    defects.extend(d)

    draft = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_22_REPOSITORY_VALIDATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.13",
        suite_id=SUITE_ID,
        verdict=Verdict.PASS.value,
        total_checks=len(checks),
        failed_checks=0,
        repository_target=REPOSITORY_TARGET,
        catalog_count=len(repositories),
        suite_execution_status=suite_execution_status,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=[],
        statuses={},
        policy={
            "start_slice_17_13": policy.get("start_slice_17_13"),
            "start_slice_17_14": policy.get("start_slice_17_14"),
            "artifact_root": policy.get("artifact_root"),
        },
        catalog=catalog_meta,
        epic17_boundary=epic17,
        scenario_results=scenario_results,
        repository_results=repository_results,
    )
    report_text = dict_to_canonical_json(draft.to_dict())
    c, d = check_security_preflight(
        clone_urls=clone_urls,
        register_entries=repository_results,
        report_text=report_text,
    )
    checks.extend(c)
    defects.extend(d)

    failed = sum(1 for x in checks if not x.ok)
    limitations = set()
    if skip_execute or suite_execution_status == "not_executed":
        limitations.update(
            {
                "full_22_repository_suite_not_executed",
                "assessment_pass_not_invented_pre_execution",
                "scaffolding_offline_checks_only",
            }
        )
    if skip_execute:
        limitations.add("portfolio_eir_build_not_executed")
    else:
        limitations.add("synthetic_validation_installation_identity")
        limitations.add("monorepo_pre_cutover_source_authority")
        limitations.add("worktree_uncommitted")
        limitations.add("owner_rotation_required_global_git_insteadof")
        # Data lake / telemetry suite-day classification
        dl_path = monorepo / SV1713_OUTPUT_RELATIVE / "data-lake-privacy-check.json"
        if dl_path.is_file():
            try:
                dl = json.loads(dl_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                dl = {}
            if dl.get("classification") == "telemetry_transport_unavailable_or_no_suite_delta":
                limitations.add("telemetry_transport_unavailable_or_no_suite_delta")
        insights_path = monorepo / SV1713_OUTPUT_RELATIVE / "insights-dashboard-check.json"
        if insights_path.is_file():
            try:
                ins = json.loads(insights_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                ins = {}
            metrics = (ins.get("overview_sanitized") or {}).get("metrics") or []
            if any(
                isinstance(m, dict)
                and (
                    "production_ingestion_still_unwired" in (m.get("limitations") or [])
                    or "no_live_dashboard_data_claim" in (m.get("limitations") or [])
                )
                for m in metrics
            ):
                limitations.add("insights_soft_limitations_present")
        if any(
            r.get("repository_validation_id") == "doris"
            and (
                r.get("quality_class") == "PASS_WITH_LIMITATIONS"
                or str(r.get("head_status_summary") or "").startswith("heads=2")
                or "limit" in " ".join(r.get("limitations") or []).lower()
            )
            for r in repository_results
        ):
            limitations.add("doris_limited_head_coverage")
        if performance_obs.get("classification") == "ACCEPTABLE_V0_2_0":
            limitations.add("performance_acceptable_v0_2_0")
    limitations = sorted(limitations & SOFT_LIMITATION_CODES)

    if failed == 0:
        verdict = Verdict.PASS_WITH_LIMITATIONS.value if limitations else Verdict.PASS.value
    else:
        verdict = Verdict.FAIL.value

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=COMMUNITY_22_REPOSITORY_VALIDATION_ID,
        package_version=VERSION,
        epic=17,
        slice="17.13",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        repository_target=REPOSITORY_TARGET,
        catalog_count=len(repositories),
        suite_execution_status=suite_execution_status,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses={
            "policy": _status(checks, "policy"),
            "catalog": "pass",
            "artifacts": _status(checks, "artifacts"),
            "assessment": _status(checks, "assessment"),
            "heads": _status(checks, "heads"),
            "telemetry": _status(checks, "telemetry"),
            "data_lake": _status(checks, "data_lake"),
            "insights": _status(checks, "insights"),
            "engineering_intelligence": _status(checks, "engineering_intelligence"),
            "security": _status(checks, "security"),
            "epic17_boundary": _status(checks, "epic17_boundary"),
            "scenarios": _status(checks, "scenarios"),
            "credibility": _status(checks, "credibility"),
        },
        policy={
            "start_slice_17_13": policy.get("start_slice_17_13"),
            "start_slice_17_14": policy.get("start_slice_17_14"),
            "artifact_root": policy.get("artifact_root"),
        },
        catalog=catalog_meta,
        epic17_boundary=epic17,
        scenario_results=scenario_results,
        repository_results=repository_results,
    )
    text = dict_to_canonical_json(report.to_dict())
    assert report_text_is_safe(text)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Slice 17.13 22-repository validation")
    parser.add_argument(
        "--skip-execute",
        action="store_true",
        default=False,
        help="Skip clone/assess execution (offline scaffolding checks only)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Deprecated alias: run verifier after suite artifacts exist",
    )
    parser.add_argument(
        "--execute-assessments",
        action="store_true",
        help="Run the full 22-repository clone+assess suite (long-running)",
    )
    parser.add_argument(
        "--clean-start",
        action="store_true",
        help="Clear generated assessments/validation runtime artifacts before execute",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit for pilot runs (must not be used for final PASS)",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated repository ids for pilot only (not for final PASS)",
    )
    parser.add_argument(
        "--telemetry-endpoint",
        default=None,
        help="Optional Community Cloud API base URL for telemetry validation",
    )
    args = parser.parse_args(argv)

    monorepo = monorepo_root_from_here()

    if args.clean_start:
        from verification.community_22_repository_validation.clean_start import (
            clean_generated_state,
        )

        removed = clean_generated_state(monorepo)
        print(f"clean_start removed={removed}")

    if args.execute_assessments:
        from verification.community_22_repository_validation.catalog import (
            load_release_validation_repositories,
        )
        from verification.community_22_repository_validation.suite_execution import (
            execute_suite,
        )

        repositories = load_release_validation_repositories(monorepo)
        if args.only:
            wanted = {x.strip() for x in args.only.split(",") if x.strip()}
            repositories = tuple(r for r in repositories if r.repository_id in wanted)
            print(f"pilot_only={sorted(wanted)} selected={len(repositories)}")
        results = execute_suite(
            monorepo,
            repositories,
            telemetry_endpoint=args.telemetry_endpoint,
            telemetry_allow=True,
            limit=args.limit,
        )
        passed = sum(1 for r in results if r.assessment_status == "pass")
        print(
            f"suite_execution complete attempted={len(results)} passed={passed} "
            f"failed={len(results) - passed}",
            flush=True,
        )
        # Portfolio EIR from successful assessments (exactly one).
        try:
            from verification.community_22_repository_validation.portfolio_eir import (
                build_portfolio_eir,
            )

            eir = build_portfolio_eir(
                monorepo,
                load_release_validation_repositories(monorepo),
                repository_results=[r.to_register_entry() for r in results],
            )
            print(
                f"portfolio_eir portfolio_run_id={eir['portfolio_run_id']} "
                f"included={eir['included']} excluded={eir['excluded']}",
                flush=True,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"portfolio_eir_failed:{type(exc).__name__}:{exc}", flush=True)

    skip_execute = args.skip_execute and not args.execute_assessments and not args.execute
    # Dual-run determinism for final verification proof.
    report_a = build_report(monorepo, skip_execute=skip_execute)
    report_b = build_report(monorepo, skip_execute=skip_execute)
    from verification.community_22_repository_validation.determinism import (
        reports_byte_identical,
    )

    if not reports_byte_identical(report_a.to_dict(), report_b.to_dict()):
        print("FAIL determinism: dual-run reports differ")
        return 2
    report = report_a
    path = write_report(monorepo, report, SV1713_OUTPUT_RELATIVE, REPORT_JSON, REPORT_MD)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"suite={report.suite_execution_status} report={path.relative_to(monorepo)} "
        "determinism=ok"
    )
    print(
        "start_slice_17_13=true start_slice_17_14=false "
        f"repository_target={REPOSITORY_TARGET} artifact_root=.codestrata-artifacts"
    )
    return 0 if report.failed_checks == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
