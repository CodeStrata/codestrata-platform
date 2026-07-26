"""Stable source-type vocabulary for Repository Knowledge documents."""

from __future__ import annotations

from enum import StrEnum


class KnowledgeSourceType(StrEnum):
    """Canonical origin kinds for knowledge documents and chunks."""

    REPOSITORY_FILE = "repository_file"
    ARCHITECTURE = "architecture"
    TECHNICAL_DEBT = "technical_debt"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    TEST = "test"
    CLOUD = "cloud"
    AI_READINESS = "ai_readiness"
    PERFORMANCE = "performance"
    FINDING = "finding"
    EVIDENCE = "evidence"
    RECOMMENDATION = "recommendation"
    REPORT_SECTION = "report_section"
