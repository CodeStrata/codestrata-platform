"""Dependency assessment factory and enablement helpers (Phase 4.4.1)."""

from __future__ import annotations

from aimf.application.dependency.assessment.assembler import (
    DependencyAssessmentAssembler,
)
from aimf.config.settings import AimfSettings, DependencyAssessmentSectionSettings


def create_dependency_assessment_assembler() -> DependencyAssessmentAssembler:
    return DependencyAssessmentAssembler()


def dependency_assessment_section_enabled(settings: AimfSettings | None) -> bool:
    if settings is None:
        return False
    return bool(settings.assessment.sections.dependency.enabled)


def dependency_pack_enabled(settings: AimfSettings | None) -> bool:
    if settings is None:
        return False
    return bool(settings.rules.enabled and settings.rules.dependency.enabled)


def dependency_assessment_section_settings(
    settings: AimfSettings | None,
) -> DependencyAssessmentSectionSettings:
    if settings is None:
        return DependencyAssessmentSectionSettings()
    return settings.assessment.sections.dependency


def configuration_fingerprint_payload(
    settings: AimfSettings | None,
    *,
    pack_enabled: bool,
) -> str:
    section = dependency_assessment_section_settings(settings)
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
