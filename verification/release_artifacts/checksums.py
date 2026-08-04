"""SHA-256 checksum registry for release artifacts and preserved inputs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from verification.release_artifacts.contract import DEMO_RELATIVE, SV12_OUTPUT_RELATIVE
from verification.release_artifacts.models import CheckResult


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def collect_checksums(
    monorepo: Path,
    *,
    artifact_paths: dict[str, str],
    demo_digests: dict[str, str],
    report_relative: str,
) -> tuple[dict[str, str], list[CheckResult]]:
    checksums: dict[str, str] = dict(demo_digests)
    checks: list[CheckResult] = []

    for label, rel in artifact_paths.items():
        path = monorepo / rel
        if path.is_file():
            checksums[rel] = sha256_file(path)
            checks.append(
                CheckResult(
                    name=f"checksums:{label}",
                    ok=True,
                    detail=f"sha256={checksums[rel][:16]}…",
                    category="checksums",
                )
            )

    for name in (
        "engineering-intelligence-report.json",
        "engineering-intelligence-report.html",
        "export-manifest.json",
    ):
        rel = f"{SV12_OUTPUT_RELATIVE}/{name}"
        path = monorepo / rel
        if path.is_file():
            checksums[rel] = sha256_file(path)
            checks.append(
                CheckResult(
                    name=f"checksums:sv12_{name}",
                    ok=True,
                    detail=f"sha256={checksums[rel][:16]}…",
                    category="checksums",
                )
            )

    report_path = monorepo / report_relative
    if report_path.is_file():
        checksums[report_relative] = sha256_file(report_path)

    demo_manifest = monorepo / DEMO_RELATIVE / "export-manifest.json"
    if demo_manifest.is_file():
        rel = f"{DEMO_RELATIVE}/export-manifest.json"
        checksums[rel] = sha256_file(demo_manifest)

    checks.append(
        CheckResult(
            name="checksums:registry_complete",
            ok=bool(checksums),
            detail=f"entries={len(checksums)}",
            category="checksums",
        )
    )
    return checksums, checks
