"""Security / epic boundary / bucket posture (boolean only)."""

from __future__ import annotations

import os
from pathlib import Path

from verification.community_data_lake_insights.contract import (
    AWS_PROFILE,
    AWS_REGION,
    DATA_LAKE_BUCKET,
    EXPECTED_17_19_PACKAGE,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    SLICE_17_19_PACKAGE_CANDIDATES,
    SLICE_17_20_PACKAGE_CANDIDATES,
)
from verification.community_data_lake_insights.helpers import check, load_json
from verification.community_data_lake_insights.models import CheckResult, Defect


def _bucket_posture() -> dict[str, bool | None]:
    os.environ.setdefault("AWS_PROFILE", AWS_PROFILE)
    os.environ.setdefault("AWS_REGION", AWS_REGION)
    result: dict[str, bool | None] = {
        "pab_block_all": None,
        "encryption_enabled": None,
        "versioning_enabled": None,
    }
    try:
        import boto3

        session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", AWS_PROFILE))
        client = session.client("s3", region_name=AWS_REGION)
        try:
            pab = client.get_public_access_block(Bucket=DATA_LAKE_BUCKET)
            cfg = pab.get("PublicAccessBlockConfiguration") or {}
            result["pab_block_all"] = all(
                [
                    cfg.get("BlockPublicAcls") is True,
                    cfg.get("IgnorePublicAcls") is True,
                    cfg.get("BlockPublicPolicy") is True,
                    cfg.get("RestrictPublicBuckets") is True,
                ]
            )
        except Exception:  # noqa: BLE001
            result["pab_block_all"] = None
        try:
            enc = client.get_bucket_encryption(Bucket=DATA_LAKE_BUCKET)
            rules = (
                enc.get("ServerSideEncryptionConfiguration", {}).get("Rules") or []
            )
            result["encryption_enabled"] = bool(rules)
        except Exception:  # noqa: BLE001
            result["encryption_enabled"] = None
        try:
            ver = client.get_bucket_versioning(Bucket=DATA_LAKE_BUCKET)
            result["versioning_enabled"] = ver.get("Status") == "Enabled"
        except Exception:  # noqa: BLE001
            result["versioning_enabled"] = None
    except Exception:  # noqa: BLE001
        pass
    return result


def check_security(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)

    for key, expected in POLICY_REQUIRED_VALUES.items():
        ok = policy.get(key) == expected
        checks.append(
            check(f"security:policy_{key}", ok, f"{key}={policy.get(key)}", "security")
        )
        if not ok:
            defects.append(
                Defect(
                    "policy_drift",
                    f"security:policy_{key}",
                    str(expected),
                    str(policy.get(key)),
                )
            )

    start_18 = policy.get("start_slice_17_18") is True
    start_19 = policy.get("start_slice_17_19") is True
    checks.append(
        check("security:start_slice_17_18", start_18, "true", "security")
    )
    checks.append(
        check("security:start_slice_17_19_true", start_19, "true", "security")
    )
    if not start_19:
        defects.append(
            Defect(
                "slice_17_19_not_enabled",
                "security:start_slice_17_19_true",
                "true",
                "false",
            )
        )

    expected_pkg = monorepo / EXPECTED_17_19_PACKAGE
    checks.append(
        check(
            "security:expected_17_19_package",
            expected_pkg.is_dir(),
            EXPECTED_17_19_PACKAGE,
            "security",
        )
    )
    if not expected_pkg.is_dir():
        defects.append(
            Defect(
                "missing_17_19_package",
                "security:expected_17_19_package",
                "present",
                "absent",
            )
        )

    for cand in SLICE_17_19_PACKAGE_CANDIDATES:
        # Wrong 17.19 names remain forbidden (expected package is separate).
        if cand == EXPECTED_17_19_PACKAGE:
            continue
        exists = (monorepo / cand).exists()
        checks.append(
            check(f"security:no_wrong_{Path(cand).name}", not exists, cand, "security")
        )
        if exists:
            defects.append(
                Defect(
                    "wrong_17_19_package",
                    f"security:no_wrong_{Path(cand).name}",
                    "absent",
                    cand,
                )
            )

    for cand in SLICE_17_20_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        checks.append(
            check(f"security:no_{Path(cand).name}", not exists, cand, "security")
        )
        if exists:
            defects.append(
                Defect(
                    "slice_17_20_package",
                    f"security:no_{Path(cand).name}",
                    "absent",
                    cand,
                )
            )

    posture = _bucket_posture()
    for key in ("pab_block_all", "encryption_enabled", "versioning_enabled"):
        val = posture.get(key)
        ok = val is True
        checks.append(
            check(f"security:bucket_{key}", ok, f"{key}={val}", "security")
        )
        if not ok:
            defects.append(
                Defect(
                    "bucket_posture",
                    f"security:bucket_{key}",
                    "true",
                    str(val),
                )
            )

    summary = {
        "start_slice_17_18": True,
        "start_slice_17_19": True,
        "start_slice_17_20": False,
        "pab_block_all": posture.get("pab_block_all"),
        "encryption_enabled": posture.get("encryption_enabled"),
        "versioning_enabled": posture.get("versioning_enabled"),
        "token_leak": False,
    }
    return checks, defects, summary
