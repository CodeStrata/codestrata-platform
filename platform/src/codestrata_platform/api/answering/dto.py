"""Answering API DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AskAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    organization_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    repository_id: str | None = Field(default=None, min_length=1)
    retrieval_index_id: str | None = Field(default=None, min_length=1)
    question_type: str | None = Field(default=None, min_length=1, max_length=64)
    canonical_ids: list[str] | None = None
    graph_node_ids: list[str] | None = None
    content_types: list[str] | None = None
    include_diagnostics: bool = False
    use_cache: bool = True


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
