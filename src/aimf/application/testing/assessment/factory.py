"""Test assessment factory and enablement helpers (Phase 4.6.1)."""

from __future__ import annotations

from aimf.application.testing.assessment.assembler import TestAssessmentAssembler
from aimf.config.settings import AimfSettings, TestingAssessmentSectionSettings


def create_testing_assessment_assembler() -> TestAssessmentAssembler:
    return TestAssessmentAssembler()


def testing_assessment_section_enabled(settings: AimfSettings | None) -> bool:
    if settings is None:
        return False
    return bool(settings.assessment.sections.testing.enabled)


def testing_pack_enabled(settings: AimfSettings | None) -> bool:
    if settings is None:
        return False
    return bool(settings.rules.enabled and settings.rules.testing.enabled)


def testing_assessment_section_settings(
    settings: AimfSettings | None,
) -> TestingAssessmentSectionSettings:
    if settings is None:
        return TestingAssessmentSectionSettings()
    return settings.assessment.sections.testing


def configuration_fingerprint_payload(
    settings: AimfSettings | None,
    *,
    pack_enabled: bool,
) -> str:
    section = testing_assessment_section_settings(settings)
    return (
        f"section_enabled={section.enabled}|"
        f"include_findings={section.include_findings}|"
        f"include_coverage={section.include_coverage}|"
        f"include_limitations={section.include_limitations}|"
        f"include_traceability={section.include_traceability}|"
        f"include_execution_summary={section.include_execution_summary}|"
        f"include_synthesis={section.include_synthesis}|"
        f"pack_enabled={pack_enabled}"
    )
