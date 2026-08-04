"""Contract / boundary / scenario / integration tests for SV.12."""

from __future__ import annotations

from pathlib import Path

from verification.engineering_intelligence_quality.contract import (
    TARGET_REPOSITORY_COUNT,
    default_contract,
)
from verification.engineering_intelligence_quality.modernization_review import (
    review_modernization,
)
from verification.engineering_intelligence_quality.pattern_review import review_patterns
from verification.engineering_intelligence_quality.capability_review import review_capability
from verification.engineering_intelligence_quality.scenarios import (
    minimal_eir_payload,
    mutate_industry_benchmark_claim,
    mutate_maturity_ranking,
    mutate_observation_without_recommendations,
    mutate_single_repo_pattern,
)
from verification.engineering_intelligence_quality.wording_review import review_wording


def test_contract_defaults() -> None:
    c = default_contract()
    assert c.target_repository_count == TARGET_REPOSITORY_COUNT == 22
    assert c.reassess_by_default is False
    assert c.clone_by_default is False
    assert c.start_sv13 is False
    assert c.redesign_report is False
    assert c.eir_schema_version == "1.0"
    assert c.assessment_schema_version == "1.2"


def test_package_outside_runtime() -> None:
    platform = Path(__file__).resolve().parents[3]
    assert (platform / "verification" / "engineering_intelligence_quality").is_dir()
    assert not (
        platform / "src" / "codestrata_platform" / "verification" / "engineering_intelligence_quality"
    ).exists()


def test_readme_exists() -> None:
    readme = (
        Path(__file__).resolve().parents[3]
        / "verification"
        / "engineering_intelligence_quality"
        / "README.md"
    )
    text = readme.read_text(encoding="utf-8")
    assert "22" in text
    assert "not" in text.lower() and "benchmark" in text.lower()


def test_single_repo_pattern_detected() -> None:
    _r, _o, defects = review_patterns(mutate_single_repo_pattern(minimal_eir_payload()))
    assert any(d.classification == "recurring_pattern" for d in defects)


def test_observation_without_recs_detected() -> None:
    _r, _o, defects = review_modernization(
        mutate_observation_without_recommendations(minimal_eir_payload())
    )
    assert any("Recommendation" in d.statement for d in defects)


def test_maturity_ranking_detected() -> None:
    _r, _o, defects = review_capability(mutate_maturity_ranking(minimal_eir_payload()))
    assert any(d.classification == "capability_comparison" for d in defects)


def test_industry_benchmark_wording_detected() -> None:
    payload = mutate_industry_benchmark_claim(minimal_eir_payload())
    _r, _o, defects = review_wording(
        json_text=str(payload),
        html_text="<html><body>This is an industry benchmark</body></html>",
    )
    assert any(d.release_impact == "blocking" for d in defects)


def test_fixture_payload_has_22_drilldowns() -> None:
    payload = minimal_eir_payload()
    assert len(payload["repository_drilldowns"]) == 22
