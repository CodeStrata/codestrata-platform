from pathlib import Path

from verification.community_insights_metrics.inventory import exists

# Mis-placed runtime package path remains forbidden; 15.10 verification package is allowed.
FORBIDDEN_NEXT = (
    "platform/src/codestrata_platform/community_insights_dashboard",
    "reports/verification/sv17-1",
)


def aggregation_absent(monorepo: Path) -> bool:
    """Prior-slice boundary: no 15.11 reports / no mis-placed dashboard runtime package."""
    return all(not exists(monorepo, rel) for rel in FORBIDDEN_NEXT)
