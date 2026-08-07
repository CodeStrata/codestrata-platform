"""SV.16 runner — release artifact verification."""

from __future__ import annotations

from pathlib import Path

from verification.release_artifacts import RELEASE_ARTIFACTS_ID
from verification.release_artifacts.checksums import collect_checksums
from verification.release_artifacts.cli import check_cli_surface
from verification.release_artifacts.contract import (
    AUTHORITATIVE_REPOSITORY_COUNT,
    DATASET_DISCLAIMER,
    INTENDED_RELEASE_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV16_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.release_artifacts.demo_artifacts import check_demo_artifacts
from verification.release_artifacts.determinism import check_determinism
from verification.release_artifacts.docker_packaging import check_docker_packaging
from verification.release_artifacts.documentation import check_documentation
from verification.release_artifacts.engineering_intelligence import check_engineering_intelligence
from verification.release_artifacts.git_state import check_git_state
from verification.release_artifacts.infrastructure_boundary import check_infrastructure_boundary
from verification.release_artifacts.installation import (
    check_installations,
    pick_primary_artifacts,
)
from verification.release_artifacts.models import Sv16VerificationReport
from verification.release_artifacts.opentofu import check_opentofu
from verification.release_artifacts.platform_boundary import check_platform_boundary
from verification.release_artifacts.public_export import check_public_export
from verification.release_artifacts.python_build import build_engine_artifacts
from verification.release_artifacts.reporting import write_verification_outputs
from verification.release_artifacts.safety import scan_artifact_paths
from verification.release_artifacts.scenarios import check_negative_scenarios
from verification.release_artifacts.schemas import check_schemas
from verification.release_artifacts.sdist import inspect_sdists
from verification.release_artifacts.verification_reports import check_verification_reports
from verification.release_artifacts.versions import check_versions
from verification.release_artifacts.vscode_extension import check_vscode_extension
from verification.release_artifacts.wheel import inspect_wheels


def run_release_artifacts(
    *,
    monorepo: Path | None = None,
    output_dir: Path | None = None,
    skip_build: bool = False,
    skip_install: bool = False,
) -> Sv16VerificationReport:
    contract = default_contract()
    assert contract.start_sv17 is False
    assert contract.no_tag is True
    assert contract.no_publish is True
    assert contract.no_deploy is True
    assert contract.no_tofu_apply is True

    root = (monorepo or monorepo_root_from_here()).resolve()
    out = (output_dir or (root / SV16_OUTPUT_RELATIVE)).resolve()

    checks = []
    defects = []
    blockers = []
    warnings = []
    limitations = []
    artifact_paths: dict[str, str] = {}
    ei_identities: dict[str, str] = {}
    demo_digests: dict[str, str] = {}

    v_checks, v_defects, v_warnings = check_versions(root)
    checks.extend(v_checks)
    defects.extend(v_defects)
    warnings.extend(v_warnings)

    g_checks, g_warnings = check_git_state(root)
    checks.extend(g_checks)
    warnings.extend(g_warnings)

    # OpenTofu before heavy wheel builds — Rosetta AWS provider handshakes are
    # more reliable when the machine is not under concurrent build pressure.
    ot_checks, ot_defects, ot_blockers, _ot_status = check_opentofu(
        waiver=contract.opentofu_waiver
    )
    checks.extend(ot_checks)
    defects.extend(ot_defects)
    blockers.extend(ot_blockers)

    wheel_paths: tuple[str, ...] = ()
    sdist_paths: tuple[str, ...] = ()
    if not skip_build:
        build, b_checks, b_defects = build_engine_artifacts(root)
        checks.extend(b_checks)
        defects.extend(b_defects)
        wheel_paths = build.wheel_paths
        sdist_paths = build.sdist_paths
        if wheel_paths:
            artifact_paths["wheel"] = wheel_paths[0]
        if sdist_paths:
            artifact_paths["sdist"] = sdist_paths[0]

        w_checks, w_defects = inspect_wheels(wheel_paths, root)
        checks.extend(w_checks)
        defects.extend(w_defects)

        s_checks, s_defects = inspect_sdists(sdist_paths, root)
        checks.extend(s_checks)
        defects.extend(s_defects)

        d_checks, d_warnings = check_determinism(
            root, wheel_paths=wheel_paths, sdist_paths=sdist_paths
        )
        checks.extend(d_checks)
        warnings.extend(d_warnings)
        limitations.extend(w.detail for w in d_warnings if w.code == "archive_timestamp_drift")

    primary_wheel, primary_sdist = pick_primary_artifacts(wheel_paths, sdist_paths)

    if not skip_install and (primary_wheel or primary_sdist):
        i_checks, i_defects, i_warnings = check_installations(
            root,
            wheel_relative=primary_wheel,
            sdist_relative=primary_sdist,
        )
        checks.extend(i_checks)
        defects.extend(i_defects)
        warnings.extend(i_warnings)

    c_checks, c_defects = check_cli_surface(root)
    checks.extend(c_checks)
    defects.extend(c_defects)

    pe_checks, pe_defects, pe_warnings = check_public_export(root)
    checks.extend(pe_checks)
    defects.extend(pe_defects)
    warnings.extend(pe_warnings)

    pb_checks, pb_defects = check_platform_boundary(
        root,
        wheel_relative=primary_wheel,
        sdist_relative=primary_sdist,
    )
    checks.extend(pb_checks)
    defects.extend(pb_defects)

    ib_checks, ib_defects = check_infrastructure_boundary(root, wheel_relative=primary_wheel)
    checks.extend(ib_checks)
    defects.extend(ib_defects)

    vs_checks, vs_defects, vs_warnings = check_vscode_extension(root)
    checks.extend(vs_checks)
    defects.extend(vs_defects)
    warnings.extend(vs_warnings)

    dk_checks, dk_warnings = check_docker_packaging(root)
    checks.extend(dk_checks)
    warnings.extend(dk_warnings)

    doc_checks, doc_defects, doc_warnings = check_documentation(root)
    checks.extend(doc_checks)
    defects.extend(doc_defects)
    warnings.extend(doc_warnings)

    sc_checks, sc_defects = check_schemas()
    checks.extend(sc_checks)
    defects.extend(sc_defects)

    vr_checks, vr_defects, vr_warnings = check_verification_reports(root)
    checks.extend(vr_checks)
    defects.extend(vr_defects)
    warnings.extend(vr_warnings)

    da_checks, da_defects, demo_digests = check_demo_artifacts(root)
    checks.extend(da_checks)
    defects.extend(da_defects)

    ei_checks, ei_defects, ei_identities = check_engineering_intelligence(root)
    checks.extend(ei_checks)
    defects.extend(ei_defects)

    checks.extend(check_negative_scenarios())

    scan_paths = tuple(artifact_paths.values())
    if scan_paths:
        sa_checks, sa_defects = scan_artifact_paths(root, scan_paths)
        checks.extend(sa_checks)
        defects.extend(sa_defects)

    confirmations = {
        "intended_release_version": INTENDED_RELEASE_VERSION,
        "engine_wheel_built": bool(artifact_paths.get("wheel")),
        "engine_sdist_built": bool(artifact_paths.get("sdist")),
        "wheel_clean_install_passed": any(
            c.name == "installation:wheel:pip_install" and c.ok for c in checks
        ),
        "sdist_clean_install_passed": any(
            c.name == "installation:sdist:pip_install" and c.ok for c in checks
        ),
        "cli_surface_verified": all(
            c.ok for c in checks if c.name.startswith("cli:")
        ),
        "platform_excluded_from_community_artifacts": all(
            c.ok for c in checks if c.name.startswith("platform_boundary:")
        ),
        "infrastructure_excluded_from_wheel": all(
            c.ok for c in checks if c.name.startswith("infrastructure_boundary:")
        ),
        "final_ei_22_repositories": all(
            c.ok
            for c in checks
            if c.name.startswith("engineering_intelligence:sv12_repository_count")
            or c.name.startswith("engineering_intelligence:sv13:")
        ),
        "sv13_ledger_closed": any(
            c.name == "verification_reports:sv13_ledger_closed" and c.ok for c in checks
        ),
        "opentofu_available": any(
            c.name == "opentofu:tool_available" and c.ok for c in checks
        ),
        "terraform_not_used_as_substitute": True,
        "no_tag": contract.no_tag,
        "no_publish": contract.no_publish,
        "no_deploy": contract.no_deploy,
        "no_tofu_apply": contract.no_tofu_apply,
        "start_sv17": contract.start_sv17,
        "opentofu_waiver": contract.opentofu_waiver,
        "no_commit_created": True,
    }

    # Collect checksums before the final write so notes/report include them.
    checksums, cs_checks = collect_checksums(
        root,
        artifact_paths=artifact_paths,
        demo_digests=demo_digests,
        report_relative=f"{SV16_OUTPUT_RELATIVE}/release-artifact-verification.json",
    )
    checks.extend(cs_checks)

    if blockers:
        verdict = "BLOCKED"
    elif any(d.release_impact == "blocking" for d in defects):
        verdict = "FAIL"
    elif limitations or any(w.release_impact != "informational" for w in warnings):
        verdict = "PASS_WITH_LIMITATIONS"
    else:
        verdict = "PASS"

    report = Sv16VerificationReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=RELEASE_ARTIFACTS_ID,
        verdict=verdict,
        intended_release_version=INTENDED_RELEASE_VERSION,
        repository_count=AUTHORITATIVE_REPOSITORY_COUNT,
        checks=checks,
        defects=defects,
        blockers=blockers,
        warnings=warnings,
        limitations=limitations,
        confirmations=confirmations,
        artifact_paths=artifact_paths,
        ei_identities=ei_identities,
        checksums=checksums,
        dataset_disclaimer=DATASET_DISCLAIMER,
    )
    write_verification_outputs(report, out)

    # Refresh report checksum after writing (digest of final JSON bytes).
    report_rel = f"{SV16_OUTPUT_RELATIVE}/release-artifact-verification.json"
    report_path = root / report_rel
    if report_path.is_file():
        from verification.release_artifacts.checksums import sha256_file

        checksums[report_rel] = sha256_file(report_path)
        report.checksums = checksums
        write_verification_outputs(report, out)
    return report
