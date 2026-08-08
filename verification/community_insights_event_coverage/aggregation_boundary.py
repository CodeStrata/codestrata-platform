from pathlib import Path

from verification.community_insights_event_coverage.inventory import exists

FORBIDDEN_NEXT = (
    "platform/src/codestrata_platform/community_insights_dashboard",
    "reports/verification/sv17-1",
)


def aggregation_absent(monorepo: Path) -> bool:
    return all(not exists(monorepo, rel) for rel in FORBIDDEN_NEXT)
