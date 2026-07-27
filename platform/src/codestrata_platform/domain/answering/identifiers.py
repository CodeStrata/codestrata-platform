"""Deterministic answering identifiers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId

_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,240}$")


def _stable_token(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]


@dataclass(frozen=True, slots=True)
class AnswerRunId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AnswerCitationId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or not _TOKEN.match(compact):
            raise InvalidValueError(
                "answer citation id is invalid",
                reason_code="invalid_answer_citation_id",
            )
        object.__setattr__(self, "value", compact)


@dataclass(frozen=True, slots=True)
class ProviderRequestId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "provider request id must be non-blank",
                reason_code="empty_provider_request_id",
            )
        object.__setattr__(self, "value", compact[:160])


@dataclass(frozen=True, slots=True)
class PromptTemplateVersion:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "prompt template version must be non-blank",
                reason_code="empty_prompt_template_version",
            )
        object.__setattr__(self, "value", compact[:64])


@dataclass(frozen=True, slots=True)
class AnswerPolicyVersion:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "answer policy version must be non-blank",
                reason_code="empty_answer_policy_version",
            )
        object.__setattr__(self, "value", compact[:64])


@dataclass(frozen=True, slots=True)
class AnswerProjectionKey:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or len(compact) > 128:
            raise InvalidValueError(
                "answer projection key is invalid",
                reason_code="invalid_answer_projection_key",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_parts(
        cls,
        *,
        organization_id: str,
        workspace_id: str,
        repository_id: str,
        retrieval_index_id: str,
        retrieval_index_version: int,
        normalized_question_hash: str,
        question_type: str,
        retrieval_policy_version: str,
        prompt_template_version: str,
        answer_policy_version: str,
        provider_id: str,
        model_id: str,
        temperature: float,
        max_output_tokens: int,
    ) -> AnswerProjectionKey:
        digest = hashlib.sha256(
            "|".join(
                [
                    organization_id.strip(),
                    workspace_id.strip(),
                    repository_id.strip(),
                    retrieval_index_id.strip(),
                    str(retrieval_index_version),
                    normalized_question_hash.strip(),
                    question_type.strip(),
                    retrieval_policy_version.strip(),
                    prompt_template_version.strip(),
                    answer_policy_version.strip(),
                    provider_id.strip(),
                    model_id.strip(),
                    f"{temperature:.3f}",
                    str(max_output_tokens),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return cls(digest)


def deterministic_answer_run_id(
    *,
    repository_id: str,
    retrieval_index_id: str,
    projection_key: str,
) -> AnswerRunId:
    token = _stable_token(repository_id, retrieval_index_id, projection_key)
    return AnswerRunId(f"eng-answer:{token}")


def normalize_question_hash(question: str) -> str:
    compact = " ".join(question.strip().lower().split())
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()
