"""Owner-review consolidated register checks."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.contract import OWNER_REGISTER_RELATIVE, OWNER_REGISTER_SCHEMA
from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect

# Required consolidated topics (must not silently disappear)
REQUIRED_TOPICS = (
    "Platform commercial/prototype packages",
    "mangum dependency debt",
    "pgvector dependency debt",
    "governance/assets amber archive",
    ".codestrata-examples",
    "Future physical repository cutovers",
    "Sample report fixture",
    "OpenTofu provider",
    "Historical verification report",
)


def check_owner_review(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / OWNER_REGISTER_RELATIVE
    add_check(checks, defects, "owner_review:register_exists", path.is_file(), OWNER_REGISTER_RELATIVE, "owner_review")
    if not path.is_file():
        return checks, defects, []
    data = load_json(path)
    add_check(
        checks,
        defects,
        "owner_review:schema",
        data.get("schema") == OWNER_REGISTER_SCHEMA,
        str(data.get("schema")),
        "owner_review",
    )
    items = data.get("items", [])
    add_check(
        checks,
        defects,
        "owner_review:non_empty",
        len(items) >= 10,
        str(len(items)),
        "owner_review",
    )
    blob = " ".join(str(i.get("topic", "")) + " " + " ".join(i.get("paths") or []) for i in items)
    for topic in REQUIRED_TOPICS:
        # fuzzy: key tokens
        key = topic.split()[0].lower()
        ok = topic.lower() in blob.lower() or key in blob.lower()
        # special cases
        if "mangum" in topic.lower():
            ok = "mangum" in blob.lower()
        elif "pgvector" in topic.lower():
            ok = "pgvector" in blob.lower()
        elif "codestrata-examples" in topic.lower():
            ok = "codestrata-examples" in blob.lower()
        elif "opentofu" in topic.lower():
            ok = "opentofu" in blob.lower() or "tofu" in blob.lower()
        elif "cutover" in topic.lower():
            ok = "cutover" in blob.lower()
        elif "amber" in topic.lower():
            ok = "amber" in blob.lower()
        elif "sample" in topic.lower():
            ok = "sample" in blob.lower() or "georgia" in blob.lower() or "fixture" in blob.lower()
        elif "historical verification" in topic.lower():
            ok = "verification report" in blob.lower() or "reports/verification" in blob.lower()
        elif "commercial" in topic.lower():
            ok = "commercial" in blob.lower() or "intelligence_reporting" in blob.lower()
        add_check(
            checks,
            defects,
            f"owner_review:topic:{key}",
            ok,
            topic,
            "owner_review",
            classification="owner_review_silently_deleted",
        )

    rules = data.get("rules") or {}
    add_check(
        checks,
        defects,
        "owner_review:no_silent_delete_rule",
        rules.get("no_silent_delete") is True,
        str(rules.get("no_silent_delete")),
        "owner_review",
    )

    # All items OPEN or DEFERRED — none silently missing ids
    ids = [i.get("id") for i in items]
    add_check(
        checks,
        defects,
        "owner_review:unique_ids",
        len(ids) == len(set(ids)),
        str(len(ids)),
        "owner_review",
    )
    return checks, defects, items
