#!/usr/bin/env python3
"""Phase 14.2 Community release validation orchestrator.

Safe: does not push, publish, create remotes, or use signing credentials.

Default steps:
  1. Release surface inventory
  2. Version consistency
  3. Dependency inventory
  4. Public export (staging)
  5. Export secret scan (blocking)
  6. validate-public-exports --skip-install
  7. SBOM generation (CycloneDX JSON)
  8. Checksums (SHA256SUMS)
  9. Provenance (release-provenance.json)

Optional:
  --with-build          build Engine sdist/wheel + record artifacts
  --with-security-check run scripts/security_check.py
  --with-verify-release also run scripts/verify_release.py --skip-export
  --skip-export         reuse existing .export-staging
  --artifact-dir PATH   output directory for release artifacts

Examples:
  python scripts/validate_release.py
  python scripts/validate_release.py --with-build
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from release import DEFAULT_ARTIFACT_DIR, RELEASE_TOOLING_VERSION  # noqa: E402
from release.checksums import verify_sha256sums, write_sha256sums  # noqa: E402
from release.dependencies import write_dependency_inventory  # noqa: E402
from release.extraction import assert_idempotent_export, tree_fingerprint  # noqa: E402
from release.inventory import load_export_manifest, write_surface_inventory  # noqa: E402
from release.licensing import check_licensing  # noqa: E402
from release.provenance import build_provenance, write_provenance  # noqa: E402
from release.sbom import generate_sboms  # noqa: E402
from release.secret_scan import scan_export_staging, write_secret_scan_report  # noqa: E402
from release.versions import check_version_consistency  # noqa: E402


def _run(argv: list[str], *, cwd: Path = ROOT) -> int:
    print("\n==>", " ".join(argv))
    completed = subprocess.run(argv, cwd=cwd, check=False)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=ROOT / DEFAULT_ARTIFACT_DIR,
        help="Directory for inventory/SBOM/checksum/provenance artifacts",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Skip export-public-repos (use existing staging)",
    )
    parser.add_argument(
        "--with-build",
        action="store_true",
        help="Build Engine sdist/wheel into artifact-dir/dist",
    )
    parser.add_argument(
        "--with-security-check",
        action="store_true",
        help="Run scripts/security_check.py",
    )
    parser.add_argument(
        "--with-verify-release",
        action="store_true",
        help="Also run scripts/verify_release.py --skip-export",
    )
    parser.add_argument(
        "--check-idempotent",
        action="store_true",
        help="Re-export once and fail if allowlisted content drifts",
    )
    args = parser.parse_args(argv)

    artifact_dir = args.artifact_dir
    artifact_dir.mkdir(parents=True, exist_ok=True)
    test_results: dict[str, object] = {
        "tooling_version": RELEASE_TOOLING_VERSION,
        "steps": {},
    }
    failures = 0

    print(f"CodeStrata release validation (tooling {RELEASE_TOOLING_VERSION})", flush=True)
    print(f"Artifacts: {artifact_dir}", flush=True)

    # 1. Surface inventory
    inventory_path = write_surface_inventory(artifact_dir / "release-surface-inventory.json")
    print(f"OK: surface inventory -> {inventory_path.name}")
    test_results["steps"]["surface_inventory"] = "passed"

    # 2. Versions
    versions = check_version_consistency(ROOT)
    (artifact_dir / "version-consistency.json").write_text(
        json.dumps(versions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if versions["passed"]:
        print("OK: version consistency")
        test_results["steps"]["version_consistency"] = "passed"
    else:
        print("FAIL: version consistency")
        for issue in versions["issues"]:
            print(f"  - {issue}")
        failures += 1
        test_results["steps"]["version_consistency"] = "failed"

    # 3. Dependencies
    dep_path = write_dependency_inventory(artifact_dir / "dependency-inventory.json")
    dep_payload = json.loads(dep_path.read_text(encoding="utf-8"))
    if dep_payload.get("passed"):
        print("OK: dependency inventory")
        test_results["steps"]["dependency_inventory"] = "passed"
    else:
        print("WARN: dependency inventory issues (non-blocking recommendations)")
        for issue in dep_payload.get("issues") or []:
            print(f"  - {issue}")
        test_results["steps"]["dependency_inventory"] = "warnings"

    if args.with_security_check:
        code = _run([sys.executable, str(SCRIPTS / "security_check.py")])
        test_results["steps"]["security_check"] = "passed" if code == 0 else "failed"
        if code != 0:
            failures += 1

    # 4. Export
    staging = ROOT / ".export-staging"
    if not args.skip_export:
        code = _run([sys.executable, str(SCRIPTS / "export-public-repos.py")])
        test_results["steps"]["export"] = "passed" if code == 0 else "failed"
        if code != 0:
            failures += 1
    else:
        test_results["steps"]["export"] = "skipped"

    # 5. Secret scan on staging
    secret_payload = scan_export_staging(staging)
    secret_path = write_secret_scan_report(secret_payload, artifact_dir / "export-secret-scan.json")
    if secret_payload.get("passed"):
        print(
            f"OK: export secret scan ({secret_payload.get('finding_count', 0)} findings, "
            f"0 blocking) -> {secret_path.name}"
        )
        test_results["steps"]["export_secret_scan"] = "passed"
    else:
        print(f"FAIL: export secret scan blocking={secret_payload.get('blocking_count')}")
        failures += 1
        test_results["steps"]["export_secret_scan"] = "failed"

    # 6. Validate exports
    code = _run(
        [
            sys.executable,
            str(SCRIPTS / "validate-public-exports.py"),
            "--skip-install",
            "--skip-export",
        ]
    )
    test_results["steps"]["validate_public_exports"] = "passed" if code == 0 else "failed"
    if code != 0:
        failures += 1

    # 6b. Licensing / required legal files on staging
    licensing = check_licensing(staging, root=ROOT)
    (artifact_dir / "licensing-check.json").write_text(
        json.dumps(licensing, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if licensing["passed"]:
        print("OK: licensing / legal files")
        test_results["steps"]["licensing"] = "passed"
    else:
        print("FAIL: licensing / legal files")
        for issue in licensing["issues"]:
            print(f"  - {issue}")
        failures += 1
        test_results["steps"]["licensing"] = "failed"

    # 6c. Optional extraction idempotency (Workstream B)
    if args.check_idempotent and not args.skip_export:
        before: dict[str, dict[str, str]] = {}
        for child in sorted(staging.iterdir()) if staging.is_dir() else []:
            if child.is_dir():
                before[child.name] = tree_fingerprint(child)
        code = _run([sys.executable, str(SCRIPTS / "export-public-repos.py")])
        idempotent_issues: list[str] = []
        if code != 0:
            idempotent_issues.append("re-export failed")
        else:
            for name, first in before.items():
                second = tree_fingerprint(staging / name)
                for err in assert_idempotent_export(first, second):
                    idempotent_issues.append(f"{name}: {err}")
        (artifact_dir / "extraction-idempotency.json").write_text(
            json.dumps(
                {"passed": not idempotent_issues, "issues": idempotent_issues},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        if idempotent_issues:
            print("FAIL: extraction idempotency")
            for issue in idempotent_issues:
                print(f"  - {issue}")
            failures += 1
            test_results["steps"]["extraction_idempotency"] = "failed"
        else:
            print("OK: extraction idempotency")
            test_results["steps"]["extraction_idempotency"] = "passed"

    # 7. SBOM
    sbom_paths = generate_sboms(artifact_dir)
    print(f"OK: generated {len(sbom_paths)} SBOM file(s)")
    test_results["steps"]["sbom"] = "passed"

    # Dependency upgrade recommendations (advisory; no auto-upgrade)
    upgrades = {
        "generated_by": "validate_release.py",
        "policy": "Do not auto-upgrade in Phase 14.2 unless release-blocking.",
        "issues": dep_payload.get("issues") or [],
        "recommendations": dep_payload.get("upgrade_recommendations") or [],
    }
    upgrade_path = artifact_dir / "dependency-upgrade-recommendations.json"
    upgrade_path.write_text(json.dumps(upgrades, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    artifact_files: list[Path] = [
        inventory_path,
        artifact_dir / "version-consistency.json",
        dep_path,
        upgrade_path,
        secret_path,
        artifact_dir / "licensing-check.json",
        *sbom_paths.values(),
    ]

    # 8. Optional package build
    if args.with_build:
        dist_dir = artifact_dir / "dist"
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        dist_dir.mkdir(parents=True, exist_ok=True)
        code = _run(
            [
                sys.executable,
                "-m",
                "build",
                "--outdir",
                str(dist_dir),
                str(ROOT / "engine"),
            ]
        )
        test_results["steps"]["python_build"] = "passed" if code == 0 else "failed"
        if code != 0:
            failures += 1
            print("FAIL: python build (is 'build' installed?)")
        else:
            artifact_files.extend(sorted(dist_dir.glob("*.whl")))
            artifact_files.extend(sorted(dist_dir.glob("*.tar.gz")))
            print("OK: python sdist/wheel")

    # Copy export manifest into artifacts for integrity set
    manifest_copy = artifact_dir / "public-export-manifest.yaml"
    shutil.copy2(ROOT / "public-export-manifest.yaml", manifest_copy)
    artifact_files.append(manifest_copy)

    # 9. Checksums (paths relative to artifact_dir, including dist/*)
    sums_path = write_sha256sums(
        artifact_files,
        artifact_dir / "SHA256SUMS",
        root=artifact_dir,
    )
    verify_errors = verify_sha256sums(sums_path, artifact_dir)
    if verify_errors:
        print("FAIL: checksum verification")
        for err in verify_errors:
            print(f"  - {err}")
        failures += 1
        test_results["steps"]["checksums"] = "failed"
    else:
        print(f"OK: SHA256SUMS ({len(artifact_files)} artifacts)")
        test_results["steps"]["checksums"] = "passed"
        artifact_files.append(sums_path)

    # 10. Provenance
    manifest = load_export_manifest(ROOT)
    provenance = build_provenance(
        artifact_dir=artifact_dir,
        artifact_files=[path for path in artifact_files if path.is_file()],
        export_manifest_version=manifest.get("version"),
        test_results=test_results,
        versions=versions,
    )
    provenance_path = write_provenance(provenance, artifact_dir / "release-provenance.json")
    # Refresh checksums to include provenance
    artifact_files.append(provenance_path)
    write_sha256sums(artifact_files, sums_path, root=artifact_dir)
    print(f"OK: provenance -> {provenance_path.name}")
    test_results["steps"]["provenance"] = "passed"

    if args.with_verify_release:
        code = _run(
            [
                sys.executable,
                str(SCRIPTS / "verify_release.py"),
                "--skip-export",
            ]
        )
        test_results["steps"]["verify_release"] = "passed" if code == 0 else "failed"
        if code != 0:
            failures += 1

    print("\n" + ("PASS" if failures == 0 else f"FAIL ({failures} step(s))"))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
