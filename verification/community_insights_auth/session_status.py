"""Session status boundary marker."""

from verification.community_insights_auth.login import check_login_logout_session

check_session_status = check_login_logout_session

__all__ = ["check_session_status"]
