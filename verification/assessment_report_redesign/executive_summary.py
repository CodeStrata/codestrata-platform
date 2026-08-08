"""Re-export presentation checks for package surface completeness."""

from verification.assessment_report_redesign.shell import (
    check_accessibility,
    check_assessment_heads,
    check_evidence,
    check_executive_summary,
    check_findings,
    check_navigation,
    check_offline,
    check_print,
    check_recommendations,
    check_responsive,
    check_scores,
    check_shell,
    check_statuses,
)

# Module aliases matching the verification package inventory.
executive_summary = check_executive_summary
assessment_heads = check_assessment_heads
findings = check_findings
evidence = check_evidence
recommendations = check_recommendations
scores = check_scores
statuses = check_statuses
navigation = check_navigation
responsive = check_responsive
print_styles = check_print
accessibility = check_accessibility
offline_boundary = check_offline

__all__ = [
    "accessibility",
    "assessment_heads",
    "check_accessibility",
    "check_assessment_heads",
    "check_evidence",
    "check_executive_summary",
    "check_findings",
    "check_navigation",
    "check_offline",
    "check_print",
    "check_recommendations",
    "check_responsive",
    "check_scores",
    "check_shell",
    "check_statuses",
    "evidence",
    "executive_summary",
    "findings",
    "navigation",
    "offline_boundary",
    "print_styles",
    "recommendations",
    "responsive",
    "scores",
    "statuses",
]
