from pathlib import Path

from verification.community_insights_metrics.inventory import exists

FORBIDDEN = (
)


def auth_package_absent(monorepo: Path) -> bool:
    return all(not exists(monorepo, rel) for rel in FORBIDDEN)
