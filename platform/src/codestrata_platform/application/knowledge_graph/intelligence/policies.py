"""Policies for graph intelligence analysis."""

from __future__ import annotations

import hashlib

from codestrata_platform.domain.knowledge_graph.analysis.impact import (
    IMPACT_POLICY_VERSION,
    DefaultImpactScoringPolicy,
)
from codestrata_platform.domain.knowledge_graph.analysis.integrity import INTEGRITY_VERSION

ANALYSIS_POLICY_VERSION = "1.0.0"


def default_impact_policy() -> DefaultImpactScoringPolicy:
    return DefaultImpactScoringPolicy(version=IMPACT_POLICY_VERSION)


def build_analysis_key(
    *,
    graph_id: str,
    graph_version: int,
    analysis_type: str,
    subject: str,
    parameters: str,
    policy_version: str,
) -> str:
    digest = hashlib.sha256(
        "|".join(
            [
                graph_id.strip(),
                str(graph_version),
                analysis_type.strip(),
                subject.strip(),
                parameters.strip(),
                policy_version.strip(),
            ]
        ).encode("utf-8")
    ).hexdigest()
    return digest


__all__ = [
    "ANALYSIS_POLICY_VERSION",
    "IMPACT_POLICY_VERSION",
    "INTEGRITY_VERSION",
    "build_analysis_key",
    "default_impact_policy",
]
