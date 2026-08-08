"""Policy registry uniqueness."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_policies(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: list[dict[str, str]] = []

    auth_root = monorepo / "platform/policies"
    mirror_root = monorepo / "insights/policies"
    add_check(checks, defects, "policies:auth_root", auth_root.is_dir(), "platform/policies", "policies")

    by_id: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(auth_root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            add_check(checks, defects, f"policies:parse:{path.name}", False, "json_error", "policies")
            continue
        pid = data.get("policy_id") or data.get("schema") or path.stem
        ver = str(data.get("policy_version") or data.get("schema") or "")
        by_id[str(pid)].append(path)
        role = "authoritative"
        summary.append(
            {
                "path": f"platform/policies/{path.name}",
                "identity": str(pid),
                "version": ver,
                "role": role,
            }
        )

    # Duplicate policy identities under authoritative root
    for pid, paths in by_id.items():
        if len(paths) > 1:
            # allow register vs policy distinct schemas sharing stem patterns carefully
            schemas = []
            for p in paths:
                try:
                    schemas.append(json.loads(p.read_text(encoding="utf-8")).get("schema"))
                except Exception:
                    schemas.append(None)
            if len(set(schemas)) < len(schemas):
                add_check(
                    checks,
                    defects,
                    f"policies:unique:{pid}",
                    False,
                    ",".join(x.name for x in paths),
                    "policies",
                    classification="duplicate_policy_authority",
                )
            else:
                add_check(
                    checks,
                    defects,
                    f"policies:unique:{pid}",
                    True,
                    "distinct_schemas",
                    "policies",
                )
        else:
            add_check(checks, defects, f"policies:unique:{pid}", True, paths[0].name, "policies")

    # Mirrors byte-identical where present
    if mirror_root.is_dir():
        for mpath in sorted(mirror_root.glob("*.json")):
            apath = auth_root / mpath.name
            if not apath.is_file():
                summary.append(
                    {
                        "path": f"insights/policies/{mpath.name}",
                        "identity": mpath.stem,
                        "version": "",
                        "role": "orphan_mirror",
                    }
                )
                add_check(
                    checks,
                    defects,
                    f"policies:mirror_has_auth:{mpath.name}",
                    False,
                    "orphan_mirror",
                    "policies",
                )
                continue
            identical = apath.read_bytes() == mpath.read_bytes()
            add_check(
                checks,
                defects,
                f"policies:mirror_identical:{mpath.name}",
                identical,
                "CONSUMER_MIRROR",
                "policies",
                classification="duplicate_policy_authority" if not identical else None,
            )
            summary.append(
                {
                    "path": f"insights/policies/{mpath.name}",
                    "identity": mpath.stem,
                    "version": "",
                    "role": "consumer_mirror",
                }
            )

    add_check(
        checks,
        defects,
        "policies:consistency_policy_present",
        (auth_root / "repository_consistency_policy.json").is_file(),
        "repository_consistency_policy.json",
        "policies",
    )
    return checks, defects, summary
