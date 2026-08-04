"""Contract constants for SV.15 deterministic output verification."""

from __future__ import annotations

from dataclasses import dataclass

from verification.deterministic_outputs import (
    DETERMINISTIC_OUTPUTS_ID,
    DETERMINISTIC_OUTPUTS_VERSION,
)

SCHEMA_NAME = "deterministic-output-verification"
SCHEMA_VERSION = "1.0.0"
TARGET_REPOSITORY_COUNT = 22

DETERMINISM_SAMPLE_IDS: tuple[str, ...] = (
    "cleanarchitecture",
    "django",
    "bookstack",
    "aspnetcore",
)

SV10_OUTPUT_RELATIVE = "engine/reports/verification/sv10"
SV10_DETERMINISM_SAMPLES = (
    "engine/reports/verification/sv10/determinism-samples.json"
)
SV11_REPORT_RELATIVE = (
    "engine/reports/verification/sv11/assessment-consistency-verification.json"
)
SV12_OUTPUT_RELATIVE = "platform/reports/verification/sv12"
SV13_OUTPUT_RELATIVE = "platform/reports/verification/sv13"
SV14_OUTPUT_RELATIVE = "platform/reports/verification/sv14"
SV15_OUTPUT_RELATIVE = "platform/reports/verification/sv15"

REPORT_JSON = "deterministic-output-verification.json"
REPORT_MD = "deterministic-output-verification.md"

DATASET_DISCLAIMER = (
    "Results describe only the 22 curated pinned repositories in the v0.2.0 "
    "release-validation catalog and are not a product-wide accuracy or "
    "industry benchmark claim."
)


@dataclass(frozen=True, slots=True)
class Sv15Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = DETERMINISTIC_OUTPUTS_ID
    package_version: str = DETERMINISTIC_OUTPUTS_VERSION
    target_repository_count: int = TARGET_REPOSITORY_COUNT
    start_sv16: bool = False
    redesign_id_schemes: bool = False
    broad_normalization: bool = False
    full_22_reassess_by_default: bool = False


def default_contract() -> Sv15Contract:
    return Sv15Contract()
