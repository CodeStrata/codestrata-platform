"""Security scan + epic boundary (start_slice_17_21 true; 17.22 false)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_ai_providers.contract import (
    EXPECTED_17_20_PACKAGE,
    EXPECTED_17_21_PACKAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    SLICE_17_22_PACKAGE_CANDIDATES,
    SV1720_OUTPUT_RELATIVE,
)
from verification.community_ai_providers.determinism import dict_to_canonical_json
from verification.community_ai_providers.helpers import (
    FORBIDDEN_REPORT_PATTERNS,
    artifact_dir,
    check,
    hard_defect,
    load_json,
    report_text_is_safe,
)
from verification.community_ai_providers.models import CheckResult, Defect


def check_security(
    monorepo: Path,
    *,
    report_preview: dict[str, Any] | None = None,
    repositories: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = load_json(monorepo / POLICY_RELATIVE)
    for key, expected in POLICY_REQUIRED_VALUES.items():
        actual = policy.get(key)
        if key == "supported_providers":
            ok = set(actual or []) == set(expected)  # type: ignore[arg-type]
        else:
            ok = actual == expected
        checks.append(
            check(f"security:policy_{key}", ok, f"{key}={actual}", "security")
        )
        if not ok:
            defects.append(
                hard_defect(
                    "policy_drift",
                    f"security:policy_{key}",
                    str(expected),
                    str(actual),
                )
            )

    start_21 = policy.get("start_slice_17_21") is True
    checks.append(
        check(
            "security:start_slice_17_21_true",
            start_21,
            "start_slice_17_21=true",
            "security",
        )
    )
    if not start_21:
        defects.append(
            hard_defect(
                "slice_17_21_not_enabled",
                "security:start_slice_17_21_true",
                "true",
                "false",
            )
        )

    expected_pkg = monorepo / EXPECTED_17_20_PACKAGE
    checks.append(
        check(
            "security:expected_17_20_package",
            expected_pkg.is_dir(),
            EXPECTED_17_20_PACKAGE,
            "security",
        )
    )
    pkg_21 = monorepo / EXPECTED_17_21_PACKAGE
    checks.append(
        check(
            "security:17_21_package_allowed",
            True,
            f"present={pkg_21.is_dir()}",
            "security",
        )
    )

    for cand in SLICE_17_22_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        checks.append(
            check(f"security:no_{Path(cand).name}", not exists, cand, "security")
        )
        if exists:
            defects.append(
                hard_defect(
                    "slice_17_22_package",
                    f"security:no_{Path(cand).name}",
                    "absent",
                    cand,
                )
            )

    report_safe = True
    if report_preview is not None:
        text = dict_to_canonical_json(report_preview)
        report_safe = report_text_is_safe(text)
        checks.append(
            check("security:report_preview_safe", report_safe, "no key patterns", "security")
        )
        if not report_safe:
            defects.append(
                hard_defect(
                    "credentials_in_report",
                    "security:report_preview_safe",
                    "safe",
                    "forbidden pattern",
                )
            )

    artifact_leaks: list[str] = []
    for item in (repositories or {}).get("selected") or []:
        for key in ("github_current", "work_no_ai", "work_bedrock"):
            base = artifact_dir(item, key, monorepo=monorepo)
            if not base:
                continue
            for name in ("assessment.json", "advisor.json"):
                path = base / name
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                for pattern in FORBIDDEN_REPORT_PATTERNS:
                    if pattern.pattern.startswith("/Users/"):
                        continue
                    if pattern.search(text):
                        artifact_leaks.append(f"{item.get('catalog_id')}:{name}")
                        break

    checks.append(
        check(
            "security:sample_artifacts_clean",
            not artifact_leaks,
            f"leaks={len(artifact_leaks)}",
            "security",
        )
    )
    if artifact_leaks:
        defects.append(
            hard_defect(
                "credentials_in_artifacts",
                "security:sample_artifacts_clean",
                "clean",
                ",".join(artifact_leaks[:5]),
            )
        )

    suite_out = monorepo / SV1720_OUTPUT_RELATIVE
    summary = {
        "start_slice_17_20": True,
        "start_slice_17_21": True,
        "start_slice_17_22": False,
        "report_safe": report_safe,
        "artifact_leaks": artifact_leaks[:10],
        "suite_output_dir": str(suite_out.relative_to(monorepo)),
    }
    return checks, defects, summary
