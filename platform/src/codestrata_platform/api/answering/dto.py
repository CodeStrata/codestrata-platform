"""Answering API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AskAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Natural-language question over repository engineering knowledge",
        examples=["What are the highest severity findings?"],
    )
    organization_id: str = Field(min_length=1, description="Organization id")
    workspace_id: str = Field(min_length=1, description="Workspace id")
    repository_id: str | None = Field(
        default=None,
        min_length=1,
        description="Repository id (required for POST /answers)",
    )
    retrieval_index_id: str | None = Field(
        default=None,
        min_length=1,
        description="Optional retrieval index pin; defaults to latest when omitted",
    )
    question_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        description="Optional question type hint",
    )
    canonical_ids: list[str] | None = Field(
        default=None,
        description="Optional canonical engineering ids to scope retrieval",
    )
    graph_node_ids: list[str] | None = Field(
        default=None,
        description="Optional knowledge-graph node ids to scope retrieval",
    )
    content_types: list[str] | None = Field(
        default=None,
        description="Optional retrieval content-type filters",
    )
    include_diagnostics: bool = Field(
        default=False,
        description="Include diagnostics in the answer payload when true",
    )
    use_cache: bool = Field(
        default=True,
        description="Allow cached answer reuse when true",
    )

class AnswerCitationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: str
    label: str
    document_id: str
    chunk_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    source_references: list[str]
    graph_node_ids: list[str]
    graph_edge_ids: list[str]
    retrieval_score: float
    excerpt: str


class EngineeringAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_run_id: str
    question: str
    question_type: str
    status: str
    answer: str | None
    citations: list[AnswerCitationResponse]
    confidence_level: str | None
    confidence_score: int | None
    grounding_status: str | None
    limitations: list[str]
    follow_up_questions: list[str]
    retrieval_index_id: str
    graph_id: str
    snapshot_id: str
    provider_id: str
    model_id: str
    prompt_template_version: str
    answer_policy_version: str
    generated_at: datetime | None
    cache_hit: bool = False
    diagnostics: dict[str, str] | None = None


class AnswerFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rating: int = Field(ge=1, le=5)
    feedback_category: str = Field(min_length=1, max_length=64)
    comment: str | None = Field(default=None, max_length=1000)


class AnswerFeedbackResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_run_id: str
    rating: int
    feedback_category: str
    comment: str
