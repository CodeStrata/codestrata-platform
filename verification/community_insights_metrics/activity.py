"""Approved activity freezes."""

from __future__ import annotations

ACTIVATION_EXCLUDED = True
EXCLUDED_ACTIVITY = (
    "extension_activate_alone",
    "open_report_alone",
    "raw_event_count_without_installation_id",
    "telemetry_housekeeping_without_approved_types",
)
