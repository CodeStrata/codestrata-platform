from pathlib import Path

from verification.community_insights_ingestion.inventory import exists

FORBIDDEN = (
    "platform/src/codestrata_platform/community_insights_dashboard",
    "reports/verification/sv17-1",
)


def dashboard_absent(monorepo: Path) -> bool:
    return all(not exists(monorepo, rel) for rel in FORBIDDEN)
