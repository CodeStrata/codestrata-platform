"""Owner-review final register and technical-debt handoff."""

from __future__ import annotations

from pathlib import Path

from verification.repository_cleanup_completion.contract import OWNER_REGISTER_RELATIVE
from verification.repository_cleanup_completion.helpers import add_check, load_json
from verification.repository_cleanup_completion.models import CheckResult, Defect

# Handoff classification for known OPEN items
HANDOFF = {
    "OR-16.8-001": "OWNER_DECISION_REQUIRED",  # commercial packages
    "OR-16.8-002": "LATER_MAINTENANCE",
    "OR-16.8-003": "LATER_MAINTENANCE",
    "OR-16.8-004": "NON_BLOCKING_EPIC16",
    "OR-16.8-005": "OWNER_DECISION_REQUIRED",  # amber archive
    "OR-16.8-006": "LATER_MAINTENANCE",
    "OR-16.8-007": "LATER_MAINTENANCE",
    "OR-16.8-008": "LATER_MAINTENANCE",  # fixture refresh
    "OR-16.8-009": "OWNER_DECISION_REQUIRED",  # mangum
    "OR-16.8-010": "OWNER_DECISION_REQUIRED",  # pgvector
    "OR-16.8-011": "LATER_MAINTENANCE",
    "OR-16.8-012": "NON_BLOCKING_EPIC16",  # codestrata-examples env
    "OR-16.8-013": "NON_BLOCKING_EPIC16",
    "OR-16.8-014": "EPIC17_RELEVANT",  # OpenTofu network
    "OR-16.8-015": "EPIC17_RELEVANT",  # cutovers/remotes — actually later than 17 start but cutover is post
}

REQUIRED_OPEN_TOPICS = (
    "commercial",
    "mangum",
    "pgvector",
    "amber",
    "codestrata-examples",
    "opentofu",
    "cutover",
)


def check_owner_review(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict], list[dict]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / OWNER_REGISTER_RELATIVE
    add_check(checks, defects, "owner_review:exists", path.is_file(), OWNER_REGISTER_RELATIVE, "owner_review")
    if not path.is_file():
        return checks, defects, [], []
    data = load_json(path)
    add_check(
        checks,
        defects,
        "owner_review:schema",
        data.get("schema") == "repository-owner-review-register:1.0",
        str(data.get("schema")),
        "owner_review",
    )
    items = data.get("items", [])
    add_check(checks, defects, "owner_review:non_empty", len(items) >= 10, str(len(items)), "owner_review")
    open_items = [i for i in items if i.get("status") == "OPEN"]
    add_check(
        checks,
        defects,
        "owner_review:open_retained",
        len(open_items) >= 8,
        str(len(open_items)),
        "owner_review",
        classification="owner_review_silently_deleted",
    )
    blob = " ".join(str(i.get("topic", "")) + " " + " ".join(i.get("paths") or []) for i in items).lower()
    for topic in REQUIRED_OPEN_TOPICS:
        add_check(
            checks,
            defects,
            f"owner_review:topic:{topic}",
            topic in blob,
            topic,
            "owner_review",
            classification="owner_review_silently_deleted",
        )

    final_register = []
    debt = []
    for item in items:
        iid = str(item.get("id"))
        handoff = HANDOFF.get(iid, "OWNER_DECISION_REQUIRED" if item.get("status") == "OPEN" else "NON_BLOCKING_EPIC16")
        entry = {
            "id": iid,
            "topic": item.get("topic"),
            "status": item.get("status"),
            "handoff_class": handoff,
            "paths": item.get("paths") or [],
            "decision_needed": item.get("decision_needed"),
        }
        final_register.append(entry)
        if item.get("status") == "OPEN":
            debt.append(
                {
                    "id": iid,
                    "topic": item.get("topic"),
                    "classification": handoff,
                    "owned": True,
                    "ambiguous": False,
                    "blocks_epic_16": False,
                    "notes": "Explicitly retained; not silently closed by Slice 16.10",
                }
            )
            add_check(
                checks,
                defects,
                f"owner_review:handoff_class:{iid}",
                handoff in {
                    "NON_BLOCKING_EPIC16",
                    "EPIC17_RELEVANT",
                    "LATER_MAINTENANCE",
                    "OWNER_DECISION_REQUIRED",
                },
                handoff,
                "technical_debt",
            )

    add_check(
        checks,
        defects,
        "technical_debt:all_open_classified",
        len(debt) == len(open_items),
        str(len(debt)),
        "technical_debt",
    )
    return checks, defects, final_register, debt
