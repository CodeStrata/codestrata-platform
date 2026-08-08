"""Logout boundary marker."""

from verification.community_insights_auth.login import check_login_logout_session

check_logout = check_login_logout_session

__all__ = ["check_logout"]
