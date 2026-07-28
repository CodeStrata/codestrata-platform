"""Platform-facing secret sanitization wrappers.

Application code imports this package (not ``codestrata.security`` directly)
to preserve application-layer import boundaries. Engine remains the source of
truth for redaction algorithms.
"""

from __future__ import annotations

from codestrata.security.database_url import sanitize_exception_message

__all__ = ["sanitize_exception_message"]
