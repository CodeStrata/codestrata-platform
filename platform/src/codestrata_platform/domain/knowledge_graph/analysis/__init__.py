"""Domain analysis package for Engineering Knowledge Graph intelligence."""

from __future__ import annotations

from codestrata_platform.domain.knowledge_graph.analysis.context import (
    HARD_MAX_DEPTH,
    HARD_MAX_EDGES,
    HARD_MAX_NODES,
    HARD_MAX_PATHS,
    GraphQueryContext,
    GraphQueryDiagnostic,
    GraphQueryLimits,
    GraphQueryScope,
    GraphQueryTrace,
    ImpactDirection,
    ImpactSeverity,
)
from codestrata_platform.domain.knowledge_graph.analysis.coverage import (
    CoverageRatio,
    GraphCoverageAnalysis,
    analyze_coverage,
)
from codestrata_platform.domain.knowledge_graph.analysis.dependency import (
    DependencyAnalysis,
    analyze_dependencies,
    detect_cycles,
)
from codestrata_platform.domain.knowledge_graph.analysis.errors import (
    GraphAnalysisError,
    GraphAnalysisLimitError,
)
from codestrata_platform.domain.knowledge_graph.analysis.impact import (
    IMPACT_POLICY_VERSION,
    ComponentImpactAnalysis,
    DefaultImpactScoringPolicy,
    FindingImpactAnalysis,
    ImpactFactor,
    ImpactScore,
    RecommendationImpactAnalysis,
    TechnologyImpactAnalysis,
    severity_band,
)
from codestrata_platform.domain.knowledge_graph.analysis.integrity import (
    INTEGRITY_VERSION,
    GraphIntegrityIssue,
    GraphIntegrityIssueType,
    GraphIntegrityReport,
    GraphIntegritySeverity,
    validate_graph_integrity,
)
from codestrata_platform.domain.knowledge_graph.analysis.ports import GraphIntelligenceRepository
from codestrata_platform.domain.knowledge_graph.analysis.risk import GraphRiskSummary, analyze_risk
from codestrata_platform.domain.knowledge_graph.analysis.traceability import (
    EvidenceTraceability,
    FindingTraceability,
    RecommendationTraceability,
    TraceabilityGap,
    detect_graph_traceability_gaps,
    trace_evidence,
    trace_finding,
    trace_recommendation,
)

__all__ = [
    "HARD_MAX_DEPTH",
    "HARD_MAX_EDGES",
    "HARD_MAX_NODES",
    "HARD_MAX_PATHS",
    "IMPACT_POLICY_VERSION",
    "INTEGRITY_VERSION",
    "ComponentImpactAnalysis",
    "CoverageRatio",
    "DefaultImpactScoringPolicy",
    "DependencyAnalysis",
    "EvidenceTraceability",
    "FindingImpactAnalysis",
    "FindingTraceability",
    "GraphAnalysisError",
    "GraphAnalysisLimitError",
    "GraphCoverageAnalysis",
    "GraphIntegrityIssue",
    "GraphIntegrityIssueType",
    "GraphIntegrityReport",
    "GraphIntegritySeverity",
    "GraphIntelligenceRepository",
    "GraphQueryContext",
    "GraphQueryDiagnostic",
    "GraphQueryLimits",
    "GraphQueryScope",
    "GraphQueryTrace",
    "GraphRiskSummary",
    "ImpactDirection",
    "ImpactFactor",
    "ImpactScore",
    "ImpactSeverity",
    "RecommendationImpactAnalysis",
    "RecommendationTraceability",
    "TechnologyImpactAnalysis",
    "TraceabilityGap",
    "analyze_coverage",
    "analyze_dependencies",
    "analyze_risk",
    "detect_cycles",
    "detect_graph_traceability_gaps",
    "severity_band",
    "trace_evidence",
    "trace_finding",
    "trace_recommendation",
    "validate_graph_integrity",
]
