"""Assessment value objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.version import PlatformVersion


@dataclass(frozen=True, slots=True)
class AssessmentVersion:
    """Version of the assessment contract / report schema produced."""

    value: str

    def __post_init__(self) -> None:
        # Reuse semantic version validation via PlatformVersion.
        version = PlatformVersion(self.value)
        object.__setattr__(self, "value", version.value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AssessmentReference:
    """External reference to Engine assessment artifacts (paths or URIs).

    Contains no findings, graphs, or RAG payloads.
    """

    artifact_uri: str
    label: str | None = None

    def __post_init__(self) -> None:
        uri = self.artifact_uri.strip()
        if not uri:
            raise InvalidValueError(
                "Assessment reference artifact URI must be non-blank",
                reason_code="empty_artifact_uri",
            )
        label = self.label.strip() if self.label else None
        if self.label is not None and not label:
            raise InvalidValueError(
                "Assessment reference label must be non-blank when provided",
                reason_code="empty_reference_label",
            )
        object.__setattr__(self, "artifact_uri", uri)
        object.__setattr__(self, "label", label)


@dataclass(frozen=True, slots=True)
class GeneratedReport:
    """Pointer to a generated customer report artifact."""

    report_type: str
    location: str

    def __post_init__(self) -> None:
        report_type = self.report_type.strip().lower()
        location = self.location.strip()
        if not report_type:
            raise InvalidValueError(
                "Generated report type must be non-blank",
                reason_code="empty_report_type",
            )
        if not location:
            raise InvalidValueError(
                "Generated report location must be non-blank",
                reason_code="empty_report_location",
            )
        object.__setattr__(self, "report_type", report_type)
        object.__setattr__(self, "location", location)


@dataclass(frozen=True, slots=True)
class AssessmentMetadata:
    attributes: Mapping[str, str]

    def __post_init__(self) -> None:
        normalized: dict[str, str] = {}
        for key, value in dict(self.attributes).items():
            compact_key = key.strip()
            compact_value = value.strip()
            if not compact_key or not compact_value:
                raise InvalidValueError(
                    "Assessment metadata keys and values must be non-blank",
                    reason_code="invalid_assessment_metadata",
                )
            normalized[compact_key] = compact_value
        object.__setattr__(self, "attributes", dict(sorted(normalized.items())))

    @classmethod
    def empty(cls) -> AssessmentMetadata:
        return cls({})
