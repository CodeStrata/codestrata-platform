"""Graph node and edge type taxonomy for CEIM projections."""

from __future__ import annotations

from enum import StrEnum


class GraphNodeType(StrEnum):
    ORGANIZATION = "organization"
    WORKSPACE = "workspace"
    REPOSITORY = "repository"
    ASSESSMENT = "assessment"
    ENGINEERING_SNAPSHOT = "engineering_snapshot"
    COMPONENT = "component"
    TECHNOLOGY = "technology"
    FRAMEWORK = "framework"
    FINDING = "finding"
    RECOMMENDATION = "recommendation"
    METRIC = "metric"
    EVIDENCE = "evidence"
    RISK = "risk"
    CAPABILITY = "capability"
    CONSTRAINT = "constraint"
    OBSERVATION = "observation"
    TAG = "tag"
    CATEGORY = "category"


class GraphEdgeType(StrEnum):
    ORGANIZATION_OWNS_WORKSPACE = "organization_owns_workspace"
    WORKSPACE_CONTAINS_REPOSITORY = "workspace_contains_repository"
    REPOSITORY_HAS_ASSESSMENT = "repository_has_assessment"
    ASSESSMENT_PRODUCES_SNAPSHOT = "assessment_produces_snapshot"

    REPOSITORY_USES_TECHNOLOGY = "repository_uses_technology"
    REPOSITORY_HAS_COMPONENT = "repository_has_component"
    REPOSITORY_HAS_FINDING = "repository_has_finding"
    REPOSITORY_HAS_RECOMMENDATION = "repository_has_recommendation"
    REPOSITORY_HAS_METRIC = "repository_has_metric"

    COMPONENT_DEPENDS_ON_COMPONENT = "component_depends_on_component"
    COMPONENT_USES_TECHNOLOGY = "component_uses_technology"
    COMPONENT_HAS_FINDING = "component_has_finding"

    FINDING_SUPPORTED_BY_EVIDENCE = "finding_supported_by_evidence"
    FINDING_CLASSIFIED_AS_CATEGORY = "finding_classified_as_category"
    FINDING_ASSOCIATED_WITH_RISK = "finding_associated_with_risk"

    RECOMMENDATION_RESOLVES_FINDING = "recommendation_resolves_finding"
    RECOMMENDATION_DEPENDS_ON_RECOMMENDATION = "recommendation_depends_on_recommendation"
    RECOMMENDATION_TARGETS_COMPONENT = "recommendation_targets_component"

    TECHNOLOGY_PART_OF_FRAMEWORK = "technology_part_of_framework"
    TECHNOLOGY_TAGGED_WITH = "technology_tagged_with"
    COMPONENT_TAGGED_WITH = "component_tagged_with"
    FINDING_TAGGED_WITH = "finding_tagged_with"

    SNAPSHOT_SUPERSEDES_SNAPSHOT = "snapshot_supersedes_snapshot"
    GRAPH_SUPERSEDES_GRAPH = "graph_supersedes_graph"


# CEIM relationship type → graph edge type (only when both endpoints exist as nodes).
CEIM_TO_GRAPH_EDGE: dict[str, GraphEdgeType] = {
    "uses": GraphEdgeType.REPOSITORY_USES_TECHNOLOGY,
    "has": GraphEdgeType.REPOSITORY_HAS_FINDING,
    "supported_by": GraphEdgeType.FINDING_SUPPORTED_BY_EVIDENCE,
    "resolves": GraphEdgeType.RECOMMENDATION_RESOLVES_FINDING,
    "depends_on": GraphEdgeType.COMPONENT_DEPENDS_ON_COMPONENT,
    "part_of": GraphEdgeType.TECHNOLOGY_PART_OF_FRAMEWORK,
    "related_to": GraphEdgeType.FINDING_ASSOCIATED_WITH_RISK,
    "tags": GraphEdgeType.FINDING_TAGGED_WITH,
}

ALLOWED_SELF_REFERENCE_EDGES = frozenset(
    {
        GraphEdgeType.COMPONENT_DEPENDS_ON_COMPONENT,
        GraphEdgeType.RECOMMENDATION_DEPENDS_ON_RECOMMENDATION,
        GraphEdgeType.SNAPSHOT_SUPERSEDES_SNAPSHOT,
        GraphEdgeType.GRAPH_SUPERSEDES_GRAPH,
    }
)
