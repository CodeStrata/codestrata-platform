"""Epic 14 policy registry."""

from __future__ import annotations

from pathlib import Path

from verification.unified_product_experience_completion.contract import EPIC14_POLICIES
from verification.unified_product_experience_completion.inventory import load_json
from verification.unified_product_experience_completion.models import CheckResult, Defect


def build_policy_registry(monorepo: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for policy_id, version, relative in EPIC14_POLICIES:
        data = load_json(monorepo, relative)
        rows.append(
            {
                "policy_id": policy_id,
                "policy_version": str(data.get("policy_version") or version),
                "source": relative,
                "observed_id": str(data.get("policy_id") or ""),
            }
        )
    return sorted(rows, key=lambda r: r["policy_id"])


def check_policy_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    rows = build_policy_registry(monorepo)
    ids = [r["policy_id"] for r in rows]
    checks.append(
        CheckResult(
            "policy_registry:no_duplicates",
            len(ids) == len(set(ids)),
            str(len(ids)),
            "policy_registry",
        )
    )
    for expected_id, expected_ver, relative in EPIC14_POLICIES:
        data = load_json(monorepo, relative)
        ok_id = data.get("policy_id") == expected_id
        ok_ver = str(data.get("policy_version")) == expected_ver
        checks.append(
            CheckResult(
                f"policy_registry:{expected_id}:id",
                ok_id,
                str(data.get("policy_id")),
                "policy_registry",
            )
        )
        checks.append(
            CheckResult(
                f"policy_registry:{expected_id}:version",
                ok_ver,
                str(data.get("policy_version")),
                "policy_registry",
            )
        )
        if not ok_id or not ok_ver:
            defects.append(
                Defect(
                    "policy_registry",
                    expected_id,
                    f"{expected_id}:{expected_ver}",
                    f"{data.get('policy_id')}:{data.get('policy_version')}",
                )
            )

    ds = load_json(monorepo, "design-system/policies/design_system_policy.json")
    checks.append(
        CheckResult(
            "policy_registry:design_system_root_authority",
            ds.get("policy_id") == "codestrata-design-system-policy"
            and ds.get("policy_version") == "1.0",
            "codestrata-design-system-policy:1.0",
            "policy_registry",
        )
    )
    # No second competing design-system policy id at root.
    competing = [
        r
        for r in rows
        if "design-system" in r["policy_id"]
        and r["policy_id"]
        not in {
            "codestrata-design-system-policy",
            "codestrata-visual-language-policy",
        }
        and "design" in r["policy_id"]
        and r["policy_id"].endswith("-design-system-policy")
    ]
    checks.append(
        CheckResult(
            "policy_registry:no_competing_design_system",
            not competing,
            "none" if not competing else competing[0]["policy_id"],
            "policy_registry",
        )
    )
    return checks, defects
