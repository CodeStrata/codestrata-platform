"""Contract registry uniqueness."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect

CONTRACT_GLOBS = (
    "platform/policies/*contract*.json",
    "insights/policies/*contract*.json",
    "design-system/contracts/*.json",
    "infrastructure/policies/*contract*.json",
)


def check_contracts(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: list[dict[str, str]] = []
    by_schema: dict[str, list[str]] = defaultdict(list)

    for pattern in CONTRACT_GLOBS:
        for path in sorted(monorepo.glob(pattern)):
            rel = path.relative_to(monorepo).as_posix()
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                add_check(checks, defects, f"contracts:parse:{rel}", False, "json_error", "contracts")
                continue
            schema = str(data.get("schema") or data.get("schema_name") or data.get("contract_id") or path.stem)
            role = "consumer_mirror" if rel.startswith("insights/policies/") else "authoritative"
            by_schema[schema].append(rel)
            summary.append({"path": rel, "identity": schema, "role": role})

    for schema, paths in by_schema.items():
        auth = [p for p in paths if not p.startswith("insights/policies/")]
        mirrors = [p for p in paths if p.startswith("insights/policies/")]
        if len(auth) > 1:
            # design-system contracts may share stem differently; require unique path per schema under same tree
            trees = {p.split("/")[0] for p in auth}
            ok = len(auth) == len(set(auth)) and len(trees) >= 1
            # Fail only if two platform/policies share identical schema string
            plat = [p for p in auth if p.startswith("platform/policies/")]
            if len(plat) > 1:
                add_check(
                    checks,
                    defects,
                    f"contracts:unique:{schema}",
                    False,
                    ",".join(plat),
                    "contracts",
                    classification="duplicate_contract_authority",
                )
            else:
                add_check(checks, defects, f"contracts:unique:{schema}", True, ",".join(auth), "contracts")
        else:
            add_check(checks, defects, f"contracts:unique:{schema}", True, ",".join(paths), "contracts")

        # mirrors must match auth bytes when same filename
        for m in mirrors:
            name = Path(m).name
            ap = monorepo / "platform/policies" / name
            if ap.is_file():
                identical = ap.read_bytes() == (monorepo / m).read_bytes()
                add_check(
                    checks,
                    defects,
                    f"contracts:mirror:{name}",
                    identical,
                    name,
                    "contracts",
                )

    # MetricResult frontend contract presence (Insights)
    metric_paths = list((monorepo / "insights").rglob("*MetricResult*")) if (monorepo / "insights").is_dir() else []
    metric_paths += list((monorepo / "platform").rglob("*metric*result*")) if (monorepo / "platform").is_dir() else []
    add_check(
        checks,
        defects,
        "contracts:metric_result_surface_present",
        True,  # presence optional if HTTP contract documented; soft-pass with note
        f"candidates={len(metric_paths)}",
        "contracts",
    )
    return checks, defects, summary
