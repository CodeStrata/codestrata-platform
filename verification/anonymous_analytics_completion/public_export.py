"""Public-export manifest checks (Slice 10.9 completion).

The six Epic 10 analytics documentation files SHOULD be present in
``public-export-manifest.yaml`` under the Engine export's ``require_files``
list. This is the one allowed packaging fix for Slice 10.9.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.models import CheckResult, Defect

REQUIRED_ANALYTICS_DOCS: tuple[str, ...] = (
    "docs/telemetry-anonymous-analytics.md",
    "docs/telemetry-installation-identity.md",
    "docs/telemetry-runtime-analytics.md",
    "docs/telemetry-assessment-analytics.md",
    "docs/telemetry-repository-aggregate-analytics.md",
    "docs/telemetry-ai-analytics.md",
)


def check_public_export(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    manifest = monorepo / "public-export-manifest.yaml"
    text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    checks.append(
        CheckResult(
            "public_export:manifest_present",
            ok=manifest.is_file(),
            category="public_export",
        )
    )

    for doc in REQUIRED_ANALYTICS_DOCS:
        ok = doc in text
        checks.append(
            CheckResult(
                f"public_export:includes:{doc.replace('/', '_').replace('.', '_')}",
                ok=ok,
                detail=doc,
                category="public_export",
            )
        )
        if not ok:
            defects.append(
                Defect("packaging/public-export defect", doc, "listed in manifest", "missing")
            )

    checks.append(
        CheckResult(
            "public_export:src_include_pattern_present",
            ok='"src/**"' in text,
            category="public_export",
        )
    )
    checks.append(
        CheckResult(
            "public_export:docs_include_pattern_present",
            ok='"docs/**"' in text,
            category="public_export",
        )
    )
    checks.append(
        CheckResult(
            "public_export:excludes_verification_reports",
            ok="reports/verification/" not in text,
            category="public_export",
        )
    )
    checks.append(
        CheckResult(
            "public_export:excludes_platform",
            ok='"platform/**"' in text,
            category="public_export",
        )
    )
    checks.append(
        CheckResult(
            "public_export:excludes_infrastructure",
            ok='"infrastructure/**"' in text,
            category="public_export",
        )
    )
    checks.append(
        CheckResult(
            "public_export:no_embedded_aws_access_key_id",
            ok="AKIA" not in text,
            category="public_export",
        )
    )

    return checks, defects
