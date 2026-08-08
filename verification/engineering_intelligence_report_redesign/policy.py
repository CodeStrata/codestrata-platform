"""Thin module surface for Slice 14.4 package inventory completeness."""

from verification.engineering_intelligence_report_redesign.checks import (
    check_assessment_boundary,
    check_design_system,
    check_determinism,
    check_domain_boundary,
    check_negative_scenarios,
    check_policy,
    check_presentation_html,
    check_renderer,
)

# Named module aliases
policy = check_policy
design_system = check_design_system
domain_boundary = check_domain_boundary
renderer = check_renderer
assessment_report_boundary = check_assessment_boundary
determinism = check_determinism
scenarios = check_negative_scenarios

__all__ = [
    "assessment_report_boundary",
    "check_assessment_boundary",
    "check_design_system",
    "check_determinism",
    "check_domain_boundary",
    "check_negative_scenarios",
    "check_policy",
    "check_presentation_html",
    "check_renderer",
    "design_system",
    "determinism",
    "domain_boundary",
    "policy",
    "renderer",
    "scenarios",
]
