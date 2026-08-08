"""Secrets Manager boundary marker."""

from verification.community_insights_auth.secret_authority import check_secret_authority

check_secrets_manager_boundary = check_secret_authority

__all__ = ["check_secrets_manager_boundary"]
