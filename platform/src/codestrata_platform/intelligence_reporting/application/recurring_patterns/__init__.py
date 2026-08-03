"""Recurring evidence-backed patterns (Platform-only).

Recurring patterns describe repeated deterministic conditions within the
selected assessed dataset. They do not establish industry prevalence,
organizational maturity, business impact, or a required portfolio action.
"""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.recurring_patterns.builder import (
    build_recurring_patterns,
    populate_report_recurring_patterns,
)
from codestrata_platform.intelligence_reporting.application.recurring_patterns.policy import (
    IDENTITY_POLICY_VERSION,
    STATEMENT_TEMPLATE_VERSION,
    RecurringPatternDiagnostics,
    RecurringPatternPolicy,
    RecurringPatternResult,
)

__all__ = [
    "IDENTITY_POLICY_VERSION",
    "STATEMENT_TEMPLATE_VERSION",
    "RecurringPatternDiagnostics",
    "RecurringPatternPolicy",
    "RecurringPatternResult",
    "build_recurring_patterns",
    "populate_report_recurring_patterns",
]
