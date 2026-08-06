"""Public-export and packaging inventory checks."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry_completion.models import CheckResult, Defect

_REQUIRED_EXPORT_DOCS = (
    "docs/telemetry.md",
    "docs/telemetry-event-catalog.md",
    "docs/telemetry-event-catalog.json",
    "docs/telemetry-preview.md",
    "docs/telemetry-transport.md",
    "docs/telemetry-assessment-isolation.md",
    "docs/telemetry-status.md",
    "docs/telemetry-pre-transport-privacy.md",
)


def check_public_export(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    manifest = monorepo / "public-export-manifest.yaml"
    text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    checks.append(
        CheckResult(
            name="public_export_manifest_present",
            ok=manifest.is_file(),
            detail="public-export-manifest.yaml",
            category="public_export",
        )
    )
    for entry in _REQUIRED_EXPORT_DOCS:
        checks.append(
            CheckResult(
                name=f"export_includes_{entry.replace('/', '_').replace('.', '_')}",
                ok=entry in text,
                detail=entry,
                category="public_export",
            )
        )
    # Must not export verification reports as include paths.
    checks.append(
        CheckResult(
            name="export_excludes_verification_reports",
            ok="reports/verification/" not in text,
            detail="reports/verification/",
            category="public_export",
        )
    )
    # Structural: no embedded AWS access-key-id material in the manifest.
    checks.append(
        CheckResult(
            name="export_excludes_embedded_aws_access_key_id",
            ok="AKIA" not in text,
            detail="aws_access_key_id_prefix_absent",
            category="public_export",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="packaging/public-export defect",
                    component="public_export",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects


def check_packaging(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    engine_pkg = monorepo / "engine" / "src" / "codestrata" / "telemetry"
    checks.append(
        CheckResult(
            name="engine_telemetry_package_present",
            ok=engine_pkg.is_dir() and (engine_pkg / "__init__.py").is_file(),
            detail="codestrata.telemetry",
            category="packaging",
        )
    )
    # No hard-coded private endpoints in transport factory.
    factory = engine_pkg / "transport_factory.py"
    if factory.is_file():
        src = factory.read_text(encoding="utf-8")
        checks.append(
            CheckResult(
                name="engine_no_hardcoded_https_endpoint",
                ok="https://" not in src and "http://" not in src,
                detail="transport_factory has no hard-coded URL",
                category="packaging",
            )
        )

    vscode_tel = monorepo / "vscode-plugin" / "src" / "telemetry"
    checks.append(
        CheckResult(
            name="vscode_telemetry_package_present",
            ok=vscode_tel.is_dir() and (vscode_tel / "index.ts").is_file(),
            detail="vscode-plugin/src/telemetry",
            category="packaging",
        )
    )
    # Capture transport must not be product default in index.
    index = (vscode_tel / "index.ts").read_text(encoding="utf-8") if vscode_tel.is_dir() else ""
    checks.append(
        CheckResult(
            name="vscode_index_exports_unavailable_default",
            ok="UnavailableExtensionTelemetryTransport" in index
            or "defaultUnavailableTransport" in index,
            detail="unavailable transport exported",
            category="packaging",
        )
    )
    # Verification packages outside product packages.
    checks.append(
        CheckResult(
            name="completion_package_outside_product",
            ok=(monorepo / "verification" / "privacy_first_telemetry_completion").is_dir()
            and not (
                monorepo
                / "engine"
                / "src"
                / "codestrata"
                / "verification"
                / "privacy_first_telemetry_completion"
            ).exists(),
            detail="top-level verification package",
            category="packaging",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="packaging/public-export defect",
                    component="packaging",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
