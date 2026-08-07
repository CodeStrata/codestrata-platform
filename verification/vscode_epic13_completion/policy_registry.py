"""Authoritative Epic 13 policy registry."""

from __future__ import annotations

from pathlib import Path

from verification.vscode_epic13_completion.contract import EPIC13_POLICIES
from verification.vscode_epic13_completion.inventory import read_text
from verification.vscode_epic13_completion.models import CheckResult, Defect

# Separately inventoried VS Code telemetry/analytics policies (not merged).
TELEMETRY_ANALYTICS_POLICIES: tuple[tuple[str, str, str], ...] = (
    (
        "vscode-telemetry-runtime-policy",
        "1.0",
        "vscode-plugin/src/telemetry/runtimePolicy.ts",
    ),
    (
        "vscode-analytics-runtime-policy",
        "1.0",
        "vscode-plugin/src/telemetry/analytics/runtimePolicy.ts",
    ),
)

STALE_DEFER_TOKENS = frozenset(
    {
        "marketplace_deferred_to_13_13",
        "marketplace_work_deferred",
        "public_cli_package_availability_deferred_to_13_14",
        "progress_ux_retained_deferred_to_13_6",
        "report_opening_ux_deferred_to_13_7",
        "epic_13_completion_deferred_to_13_15",
    }
)


def build_policy_registry(monorepo: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy_id, version, source in EPIC13_POLICIES:
        rows.append(
            {
                "policy_id": policy_id,
                "policy_version": version,
                "source": source,
                "family": "epic13_slice",
            }
        )
    for policy_id, version, source in TELEMETRY_ANALYTICS_POLICIES:
        rows.append(
            {
                "policy_id": policy_id,
                "policy_version": version,
                "source": source,
                "family": "vscode_telemetry_analytics",
            }
        )
    return sorted(rows, key=lambda r: (r["family"], r["policy_id"]))


def check_policy_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ids: list[str] = []

    for policy_id, version, source in EPIC13_POLICIES:
        ids.append(policy_id)
        path = monorepo / source
        present = path.is_file()
        text = path.read_text(encoding="utf-8") if present else ""
        version_ok = present and (
            f'POLICY_VERSION = "{version}"' in text
            or f'policy_version: "{version}"' in text
            or f'="{version}" as const' in text
            or f'= "{version}" as const' in text
        )
        id_ok = present and policy_id in text
        stale = sorted(t for t in STALE_DEFER_TOKENS if t in text)
        checks.append(
            CheckResult(
                name=f"policy:{policy_id}:present",
                ok=present and id_ok,
                detail="present" if present else "missing",
                category="policy_registry",
            )
        )
        checks.append(
            CheckResult(
                name=f"policy:{policy_id}:version",
                ok=version_ok,
                detail=version if version_ok else "drift",
                category="policy_registry",
            )
        )
        checks.append(
            CheckResult(
                name=f"policy:{policy_id}:no_stale_deferral",
                ok=not stale,
                detail=",".join(stale) if stale else "clean",
                category="policy_registry",
            )
        )
        if not present or not id_ok:
            defects.append(
                Defect(
                    classification="documentation_drift",
                    surface=source,
                    expected=policy_id,
                    observed="missing",
                )
            )
        if present and not version_ok:
            defects.append(
                Defect(
                    classification="prior-slice product defect",
                    surface=source,
                    expected=f"version {version}",
                    observed="version drift",
                )
            )
        if stale:
            defects.append(
                Defect(
                    classification="documentation_drift",
                    surface=source,
                    expected="no stale deferral tokens",
                    observed=",".join(stale),
                )
            )

    for policy_hint, _ver, source in TELEMETRY_ANALYTICS_POLICIES:
        text = read_text(monorepo, source) if (monorepo / source).is_file() else ""
        ok = (monorepo / source).is_file() and "1.0" in text
        checks.append(
            CheckResult(
                name=f"policy_aux:{policy_hint}:present",
                ok=ok,
                detail="inventoried_separately",
                category="policy_registry",
            )
        )

    unique = len(ids) == len(set(ids)) and len(ids) == 14
    checks.append(
        CheckResult(
            name="policy:count_14_unique",
            ok=unique,
            detail=str(len(set(ids))),
            category="policy_registry",
        )
    )
    if not unique:
        defects.append(
            Defect(
                classification="completion harness defect",
                surface="policy_registry",
                expected="14 unique Epic 13 policies",
                observed=str(ids),
            )
        )
    return checks, defects
