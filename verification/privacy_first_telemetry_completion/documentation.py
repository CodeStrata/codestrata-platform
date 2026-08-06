"""Documentation consistency for Epic 9 completion."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry_completion.models import CheckResult, Defect

_REQUIRED_ENGINE_DOCS = (
    "telemetry.md",
    "telemetry-runtime.md",
    "telemetry-disabled-default.md",
    "telemetry-session-consent.md",
    "telemetry-interactive-consent.md",
    "telemetry-non-interactive.md",
    "telemetry-cli-consent-flags.md",
    "telemetry-status.md",
    "telemetry-event-catalog.md",
    "telemetry-preview.md",
    "telemetry-pre-transport-privacy.md",
    "telemetry-transport.md",
    "telemetry-assessment-isolation.md",
)

_REQUIRED_PHRASES = (
    "disabled by default",
    "installation",
)

_FORBIDDEN_CLAIMS = (
    "production telemetry is operational",
    "telemetry is enabled by default",
    "consent is remembered",
    "consent is saved permanently",
    "vs code transmitting",
    "cursor telemetry available",
    "installation id is active",
)


def check_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    docs_dir = monorepo / "engine" / "docs"

    for name in _REQUIRED_ENGINE_DOCS:
        path = docs_dir / name
        checks.append(
            CheckResult(
                name=f"doc_present_{name.replace('.', '_').replace('-', '_')}",
                ok=path.is_file(),
                detail=name,
                category="documentation",
            )
        )

    # Aggregate public docs text for claim scanning (engine + vscode).
    blobs: list[str] = []
    for name in _REQUIRED_ENGINE_DOCS:
        path = docs_dir / name
        if path.is_file():
            blobs.append(path.read_text(encoding="utf-8").lower())
    vscode_doc = monorepo / "vscode-plugin" / "docs" / "telemetry.md"
    if vscode_doc.is_file():
        blobs.append(vscode_doc.read_text(encoding="utf-8").lower())
        checks.append(
            CheckResult(
                name="doc_vscode_telemetry_present",
                ok=True,
                detail="vscode-plugin/docs/telemetry.md",
                category="documentation",
            )
        )
    else:
        checks.append(
            CheckResult(
                name="doc_vscode_telemetry_present",
                ok=False,
                detail="missing",
                category="documentation",
            )
        )

    combined = "\n".join(blobs)
    checks.append(
        CheckResult(
            name="docs_state_disabled_by_default",
            ok="disabled by default" in combined or "disabled-by-default" in combined,
            detail="disabled-by-default posture documented",
            category="documentation",
        )
    )
    checks.append(
        CheckResult(
            name="docs_no_installation_identity_active",
            ok="installation identity" in combined or "no installation" in combined
            or "installation_id" in combined
            or "not used" in combined,
            detail="installation identity documented as unused/forbidden",
            category="documentation",
        )
    )

    for claim in _FORBIDDEN_CLAIMS:
        checks.append(
            CheckResult(
                name=f"docs_forbid_{claim.replace(' ', '_')[:40]}",
                ok=claim not in combined,
                detail=claim,
                category="documentation",
            )
        )

    # VS Code docs must not claim active transmission.
    if vscode_doc.is_file():
        vs = vscode_doc.read_text(encoding="utf-8").lower()
        checks.append(
            CheckResult(
                name="docs_vscode_unavailable_transport",
                ok="unavailable" in vs and ("no http" in vs or "http" in vs),
                detail="VS Code docs describe unavailable/no HTTP transport",
                category="documentation",
            )
        )
        checks.append(
            CheckResult(
                name="docs_vscode_not_claiming_active_collection",
                ok="currently collecting" not in vs and "telemetry is enabled" not in vs,
                detail="no active collection claim",
                category="documentation",
            )
        )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="documentation inconsistency",
                    component="docs",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
