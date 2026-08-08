"""API protection checks."""

from verification.community_insights_auth.middleware import check_authorization

check_api_protection = check_authorization

__all__ = ["check_api_protection"]
