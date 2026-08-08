"""Privacy boundary checks."""

from verification.community_insights_auth.api_client import check_api_client
from verification.community_insights_auth.secret_authority import check_secret_authority


def check_privacy_boundary(monorepo):
    checks: list = []
    defects: list = []
    for fn in (check_secret_authority, check_api_client):
        c, d = fn(monorepo)
        checks.extend(c)
        defects.extend(d)
    return checks, defects
