from pathlib import Path

from verification.community_insights_metrics.inventory import exists

FORBIDDEN = (
    "platform/src/codestrata_platform/community_insights_dashboard",
    "reports/verification/sv17-1",
)


def dashboard_absent(monorepo: Path) -> bool:
    """True when 15.11 has not started and no mis-placed dashboard package exists."""
    return all(not exists(monorepo, rel) for rel in FORBIDDEN)
