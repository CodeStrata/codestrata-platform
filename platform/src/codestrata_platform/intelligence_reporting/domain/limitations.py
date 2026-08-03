"""Structured dataset / report limitations (interpretation impact)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    bound_statement,
    optional_sorted_ids,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    LimitationCategory,
    LimitationSeverity,
)
from codestrata_platform.intelligence_reporting.domain.identifiers import (
    LimitationId,
    build_limitation_id,
)


@dataclass(frozen=True, slots=True)
class DatasetLimitation:
    limitation_id: LimitationId
    category: LimitationCategory
    severity: LimitationSeverity
    statement: str
    affected_repository_ids: tuple[str, ...] = ()
    affected_assessment_head_ids: tuple[str, ...] = ()
    affected_observation_ids: tuple[str, ...] = ()
    remediation_or_interpretation: str | None = None
    customer_visible: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "statement", bound_statement(self.statement))
        object.__setattr__(
            self,
            "affected_repository_ids",
            optional_sorted_ids(
                self.affected_repository_ids, label="affected_repository_id"
            ),
        )
        object.__setattr__(
            self,
            "affected_assessment_head_ids",
            optional_sorted_ids(
                self.affected_assessment_head_ids, label="affected_assessment_head_id"
            ),
        )
        object.__setattr__(
            self,
            "affected_observation_ids",
            optional_sorted_ids(
                self.affected_observation_ids, label="affected_observation_id"
            ),
        )
        if self.remediation_or_interpretation is not None:
            object.__setattr__(
                self,
                "remediation_or_interpretation",
                bound_statement(self.remediation_or_interpretation),
            )
        expected = build_limitation_id(
            category=self.category.value,
            statement=self.statement,
            affected_repository_ids=self.affected_repository_ids,
        )
        if self.limitation_id.value != expected.value:
            raise InvalidValueError(
                "limitation_id does not match category/statement/affected repositories",
                reason_code="unstable_limitation_id",
            )

    @classmethod
    def create(
        cls,
        *,
        category: LimitationCategory,
        severity: LimitationSeverity,
        statement: str,
        affected_repository_ids: Sequence[str] = (),
        affected_assessment_head_ids: Sequence[str] = (),
        affected_observation_ids: Sequence[str] = (),
        remediation_or_interpretation: str | None = None,
        customer_visible: bool = True,
    ) -> DatasetLimitation:
        statement_text = bound_statement(statement)
        repos = optional_sorted_ids(affected_repository_ids, label="affected_repository_id")
        return cls(
            limitation_id=build_limitation_id(
                category=category.value,
                statement=statement_text,
                affected_repository_ids=repos,
            ),
            category=category,
            severity=severity,
            statement=statement_text,
            affected_repository_ids=repos,
            affected_assessment_head_ids=tuple(affected_assessment_head_ids),
            affected_observation_ids=tuple(affected_observation_ids),
            remediation_or_interpretation=remediation_or_interpretation,
            customer_visible=customer_visible,
        )
