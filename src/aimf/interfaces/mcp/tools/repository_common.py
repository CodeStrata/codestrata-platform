"""Shared helpers for repository-intelligence MCP tools."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aimf.application.knowledge.queries import KnowledgeQueryService
from aimf.application.knowledge.queries.models import FindingView, RecommendationView
from aimf.domain.knowledge.answering import AnswerStatus
from aimf.domain.knowledge.retrieval import (
    RetrievalFilters,
    RetrievalScope,
    RetrievalStatus,
)
from aimf.interfaces.mcp.envelope import (
    McpCoverage,
    McpDiagnostic,
    McpToolResponse,
    McpToolStatus,
    envelope,
)
from aimf.interfaces.mcp.mapping import to_mcp_payload
from aimf.interfaces.mcp.security import optional_filter, require_nonblank
from aimf.services.artifact_serialization import dumps_stable_json

PACK_CATEGORY_ALIASES: dict[str, frozenset[str]] = {
    "architecture": frozenset({"architecture", "structural"}),
    "security": frozenset({"security"}),
    "dependencies": frozenset({"dependency", "dependencies"}),
    "tests": frozenset({"test", "testing", "tests"}),
    "cloud": frozenset({"cloud"}),
    "ai_readiness": frozenset({"ai_readiness", "ai-readiness", "ai"}),
    "performance": frozenset({"performance"}),
    "technical_debt": frozenset({"technical_debt", "tech_debt", "debt"}),
}

DEFAULT_LIMITATIONS = (
    "MCP tools are read-only adapters over existing CodeStrata services.",
    "Outputs are scoped to tenant_id + repository_id; no cross-repository leakage.",
    "repository_answer uses deterministic extractive answering (not generative AI).",
)


def require_scope(*, tenant_id: str, repository_id: str) -> tuple[str, str]:
    return (
        require_nonblank(tenant_id, label="tenant_id"),
        require_nonblank(repository_id, label="repository_id"),
    )


def build_scope(
    *,
    tenant_id: str,
    repository_id: str,
    scan_id: str | None = None,
    branch: str | None = None,
    commit_sha: str | None = None,
) -> RetrievalScope:
    tenant, repo = require_scope(tenant_id=tenant_id, repository_id=repository_id)
    return RetrievalScope(
        tenant_id=tenant,
        repository_id=repo,
        scan_id=optional_filter(scan_id, label="scan_id"),
        branch=optional_filter(branch, label="branch"),
        commit_sha=optional_filter(commit_sha, label="commit_sha"),
    )


def build_filters(
    *,
    source_types: Sequence[str] | None = None,
    intelligence_packs: Sequence[str] | None = None,
    severities: Sequence[str] | None = None,
    file_paths: Sequence[str] | None = None,
    symbol_names: Sequence[str] | None = None,
    finding_ids: Sequence[str] | None = None,
    rule_ids: Sequence[str] | None = None,
) -> RetrievalFilters:
    return RetrievalFilters(
        source_types=tuple(source_types or ()),
        intelligence_packs=tuple(intelligence_packs or ()),
        severities=tuple(severities or ()),
        file_paths=tuple(file_paths or ()),
        symbol_names=tuple(symbol_names or ()),
        finding_ids=tuple(finding_ids or ()),
        rule_ids=tuple(rule_ids or ()),
    )


def map_retrieval_status(status: RetrievalStatus) -> McpToolStatus:
    mapping = {
        RetrievalStatus.SUCCESS: McpToolStatus.SUCCESS,
        RetrievalStatus.PARTIAL: McpToolStatus.PARTIAL,
        RetrievalStatus.EMPTY: McpToolStatus.EMPTY,
        RetrievalStatus.FAILED: McpToolStatus.FAILED,
        RetrievalStatus.DISABLED: McpToolStatus.DISABLED,
    }
    return mapping.get(status, McpToolStatus.FAILED)


def map_answer_status(status: AnswerStatus) -> McpToolStatus:
    mapping = {
        AnswerStatus.SUCCESS: McpToolStatus.SUCCESS,
        AnswerStatus.PARTIAL: McpToolStatus.PARTIAL,
        AnswerStatus.EMPTY: McpToolStatus.EMPTY,
        AnswerStatus.INSUFFICIENT_EVIDENCE: McpToolStatus.INSUFFICIENT_EVIDENCE,
        AnswerStatus.FAILED: McpToolStatus.FAILED,
        AnswerStatus.DISABLED: McpToolStatus.DISABLED,
    }
    return mapping.get(status, McpToolStatus.FAILED)


def disabled_response(
    tool_name: str,
    *,
    code: str,
    message: str,
    request_payload: Mapping[str, Any],
) -> dict[str, Any]:
    response = envelope(
        tool_name=tool_name,
        status=McpToolStatus.DISABLED,
        data={},
        diagnostics=(McpDiagnostic(code=code, message=message, severity="info"),),
        limitations=DEFAULT_LIMITATIONS,
        request_payload=request_payload,
    )
    payload = to_mcp_payload(response)
    assert isinstance(payload, dict)
    return payload


def failed_response(
    tool_name: str,
    *,
    code: str,
    message: str,
    request_payload: Mapping[str, Any],
) -> dict[str, Any]:
    response = envelope(
        tool_name=tool_name,
        status=McpToolStatus.FAILED,
        data={},
        diagnostics=(McpDiagnostic(code=code, message=message, severity="error"),),
        limitations=DEFAULT_LIMITATIONS,
        request_payload=request_payload,
    )
    payload = to_mcp_payload(response)
    assert isinstance(payload, dict)
    return payload


def bound_payload(
    tool_name: str,
    *,
    status: McpToolStatus,
    data: Mapping[str, Any],
    request_payload: Mapping[str, Any],
    max_characters: int,
    diagnostics: Sequence[McpDiagnostic] = (),
    limitations: Sequence[str] = DEFAULT_LIMITATIONS,
    result_count: int | None = None,
) -> dict[str, Any]:
    """Serialize data; if oversized, omit lower-priority list keys entirely."""

    payload = dict(data)
    text = dumps_stable_json(to_mcp_payload(payload))
    excluded = 0
    truncated = False
    diags = list(diagnostics)
    if len(text) > max_characters:
        truncated = True
        for key in ("hits", "findings", "recommendations", "files", "evidence", "statements"):
            if key in payload and isinstance(payload[key], list) and payload[key]:
                excluded += len(payload[key])
                payload[key] = []
                diags.append(
                    McpDiagnostic(
                        code="result_too_large",
                        message=f"omitted {key} to satisfy max_result_characters",
                        severity="warning",
                    )
                )
                text = dumps_stable_json(to_mcp_payload(payload))
                if len(text) <= max_characters:
                    break
        if len(text) > max_characters:
            payload = {"bounded": True, "message": "result exceeded max_result_characters"}
            excluded += 1
            status = McpToolStatus.PARTIAL
    count = result_count if result_count is not None else _infer_count(payload)
    if truncated and status == McpToolStatus.SUCCESS:
        status = McpToolStatus.PARTIAL
    response = envelope(
        tool_name=tool_name,
        status=status,
        data=payload,
        coverage=McpCoverage(
            result_count=count,
            result_characters=len(dumps_stable_json(to_mcp_payload(payload))),
            truncated=truncated,
            excluded_count=excluded,
        ),
        diagnostics=tuple(diags),
        limitations=limitations,
        request_payload=request_payload,
    )
    out = to_mcp_payload(response)
    assert isinstance(out, dict)
    return out


def _infer_count(payload: Mapping[str, Any]) -> int:
    for key in ("hits", "findings", "recommendations", "files", "statements", "packs"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    return 1 if payload else 0


def resolve_latest_run_id(
    queries: KnowledgeQueryService,
    repository_id: str,
) -> str | None:
    try:
        latest = queries.get_latest_completed_run(repository_id)
    except Exception:  # noqa: BLE001 - unknown repo / store errors → empty
        return None
    if latest is None:
        return None
    return latest.run_id


def filter_findings(
    findings: Sequence[FindingView],
    *,
    intelligence_pack: str | None = None,
    severity: str | None = None,
    finding_id: str | None = None,
    rule_id: str | None = None,
    file_path: str | None = None,
) -> list[FindingView]:
    pack = optional_filter(intelligence_pack, label="intelligence_pack")
    sev = optional_filter(severity, label="severity")
    fid = optional_filter(finding_id, label="finding_id")
    rid = optional_filter(rule_id, label="rule_id")
    path = optional_filter(file_path, label="file_path")
    aliases = PACK_CATEGORY_ALIASES.get(pack or "", frozenset())
    out: list[FindingView] = []
    for item in findings:
        if fid is not None and item.finding_id != fid:
            continue
        if rid is not None and item.rule_id != rid:
            continue
        if sev is not None and item.severity.lower() != sev.lower():
            continue
        if pack is not None:
            category = item.category.lower()
            if aliases:
                if category not in aliases and pack.lower() not in category:
                    continue
            elif pack.lower() not in category:
                continue
        if path is not None:
            haystacks = " ".join(
                [
                    " ".join(item.subject_ids),
                    str(item.metadata.get("file_path", "")),
                    str(item.metadata.get("path", "")),
                ]
            )
            if path not in haystacks:
                continue
        out.append(item)
    return sorted(out, key=lambda item: (item.severity, item.finding_id, item.rule_id))


def filter_recommendations(
    recommendations: Sequence[RecommendationView],
    *,
    intelligence_pack: str | None = None,
    severity: str | None = None,
    finding_id: str | None = None,
) -> list[RecommendationView]:
    pack = optional_filter(intelligence_pack, label="intelligence_pack")
    sev = optional_filter(severity, label="severity")
    fid = optional_filter(finding_id, label="finding_id")
    aliases = PACK_CATEGORY_ALIASES.get(pack or "", frozenset())
    out: list[RecommendationView] = []
    for item in recommendations:
        if fid is not None and fid not in item.related_finding_ids:
            continue
        if sev is not None and item.priority.lower() != sev.lower():
            continue
        if pack is not None:
            category = item.category.lower()
            if aliases:
                if category not in aliases and pack.lower() not in category:
                    continue
            elif pack.lower() not in category:
                continue
        out.append(item)
    return sorted(
        out,
        key=lambda item: (item.priority, item.recommendation_id, item.category),
    )


def strip_embeddings(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {
            key: strip_embeddings(value)
            for key, value in payload.items()
            if key not in {"embedding", "embeddings", "vector", "vectors"}
        }
    if isinstance(payload, list):
        return [strip_embeddings(item) for item in payload]
    return payload


def response_dict(response: McpToolResponse) -> dict[str, Any]:
    payload = to_mcp_payload(response)
    assert isinstance(payload, dict)
    return payload
