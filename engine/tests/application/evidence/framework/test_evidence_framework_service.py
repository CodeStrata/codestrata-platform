from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from codestrata.application.evidence.framework.service import EvidenceFrameworkService
from codestrata.domain.evidence.framework.models import (
    AssessmentResult,
    EvidenceActivity,
    EvidenceImport,
    SensitivityPolicy,
)


def _repository(path: Path) -> Path:
    (path / "src").mkdir(parents=True)
    (path / "tests").mkdir()
    (path / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\ndependencies = ["pydantic>=2"]\n',
        encoding="utf-8",
    )
    (path / "src" / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (path / "tests" / "test_app.py").write_text(
        "def test_answer():\n    assert 42 == 42\n", encoding="utf-8"
    )
    return path


def test_default_plan_runs_to_portable_artifact_set(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    service = EvidenceFrameworkService()
    plan = service.create_default_plan(repository)
    events = []
    result = service.run(
        plan,
        output_root=tmp_path / "artifacts",
        on_event=events.append,
    )
    assert result.run.status.value == "completed"
    assert len(result.evidence) == 3
    assert {item.outcome.value for item in result.assessment.claims} == {
        "supported",
        "not_assessed",
    }
    assert result.assessment.findings[0].claim_id == "decision.user-goal"
    assert result.assessment.actions[0].title == (
        "Select a decision-specific assessment profile"
    )
    assert events[0].status.value == "running"
    required = {
        "plan.yaml",
        "run.json",
        "evidence.jsonl",
        "coverage.json",
        "assessment.json",
        "report.html",
        "report.sarif",
        "raw",
    }
    assert {item.name for item in result.output_directory.iterdir()} == required
    assert (result.output_directory.stat().st_mode & 0o077) == 0
    assert ((result.output_directory / "evidence.jsonl").stat().st_mode & 0o077) == 0
    html = (result.output_directory / "report.html").read_text(encoding="utf-8")
    assert "Claims and arguments" in html
    assert "Guiding actions" in html
    assert "Evidence collected; decision not assessed" in html
    assert "test candidates" in html
    assert "The complete typed payloads are in" in html
    assert "No universal repository quality score" in html


def test_sarif_import_preserves_raw_and_creates_traceable_action(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "fixture-analyzer", "version": "1.2"}},
                "results": [
                    {
                        "ruleId": "FIX001",
                        "level": "warning",
                        "message": {"text": "Review this code."},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "src/app.py"},
                                    "region": {"startLine": 1},
                                }
                            }
                        ],
                        "partialFingerprints": {"primary": "stable"},
                    }
                ],
            }
        ],
    }
    (repository / "analysis.sarif").write_text(json.dumps(sarif), encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(repository)
    plan = base.model_copy(
        update={
            "imports": (
                EvidenceImport(import_id="fixture", path="analysis.sarif"),
            )
        }
    )
    result = service.run(plan, output_root=tmp_path / "artifacts")
    imported = [item for item in result.evidence if item.kind == "analysis.finding"]
    assert len(imported) == 1
    assert imported[0].raw_references[0].sha256
    assert imported[0].payload["fingerprints"] == {"primary": "stable"}
    assert any(
        item.evidence_ids == (imported[0].evidence_id,)
        for item in result.assessment.findings
    )
    known_claim_ids = {item.claim_id for item in result.assessment.claims}
    assert all(item.claim_id in known_claim_ids for item in result.assessment.findings)
    assert result.assessment.actions
    assert any(
        item.finding_id
        == next(
            finding.finding_id
            for finding in result.assessment.findings
            if finding.evidence_ids == (imported[0].evidence_id,)
        )
        for item in result.assessment.risks
    )
    raw_path = result.output_directory / imported[0].raw_references[0].relative_path
    assert raw_path.read_text(encoding="utf-8") == json.dumps(sarif)
    exported = json.loads((result.output_directory / "report.sarif").read_text())
    assert exported["version"] == "2.1.0"
    assert exported["runs"][0]["results"][0]["locations"][0]


def test_preview_blocks_external_tool_when_network_is_denied(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(repository)
    trivy = EvidenceActivity(
        activity_id="trivy",
        collector_id="external.trivy",
        configuration={"scanners": ["misconfig"]},
    )
    plan = base.model_copy(
        update={"activities": (*base.activities, trivy)}
    )
    preview = service.preview(plan)
    row = next(item for item in preview.collectors if item.activity_id == "trivy")
    assert row.status in {"blocked", "unavailable"}
    assert any("Trivy" in item for item in preview.leaves_machine)


def test_external_collector_retains_native_output_by_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _repository(tmp_path / "repo")
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "Trivy", "version": "fixture"}},
                "results": [
                    {
                        "ruleId": "TRIVY-001",
                        "level": "warning",
                        "message": {"text": "Fixture result."},
                    }
                ],
            }
        ],
    }
    native_output = json.dumps(sarif)
    monkeypatch.setattr(
        "codestrata.application.evidence.framework.collectors.shutil.which",
        lambda _: "/usr/local/bin/trivy",
    )
    monkeypatch.setattr(
        "codestrata.application.evidence.framework.collectors.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=native_output,
            stderr="",
        ),
    )
    service = EvidenceFrameworkService()
    base = service.create_default_plan(repository)
    plan = base.model_copy(
        update={
            "activities": (
                EvidenceActivity(
                    activity_id="trivy",
                    collector_id="external.trivy",
                    configuration={"scanners": ["misconfig"]},
                ),
            ),
            "limits": base.limits.model_copy(update={"external_access": "allow"}),
        }
    )
    result = service.run(plan, output_root=tmp_path / "artifacts")
    assert len(result.evidence) == 1
    raw_reference = result.evidence[0].raw_references[0]
    assert raw_reference.storage_mode == "copied"
    assert (
        result.output_directory / raw_reference.relative_path
    ).read_text(encoding="utf-8") == native_output


def test_unknown_assessment_profile_fails_before_collection(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    service = EvidenceFrameworkService()
    plan = service.create_default_plan(repository).model_copy(
        update={"assessment_profile": "imaginary-readiness@9.9"}
    )
    with pytest.raises(ValueError, match="unknown assessment profile"):
        service.preview(plan)


def test_dependency_source_snippets_are_not_stored_by_default(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    result = EvidenceFrameworkService().run(
        EvidenceFrameworkService().create_default_plan(repository),
        output_root=tmp_path / "artifacts",
    )
    dependency = next(item for item in result.evidence if item.kind == "repository.dependencies")

    def snippets(value: object) -> list[object]:
        if isinstance(value, dict):
            return [
                child
                for key, child in value.items()
                if key == "snippet"
            ] + [nested for child in value.values() for nested in snippets(child)]
        if isinstance(value, list):
            return [nested for child in value for nested in snippets(child)]
        return []

    assert snippets(dependency.payload)
    assert set(snippets(dependency.payload)) <= {
        None,
        "[not stored by evidence policy]",
    }
    assert "source snippets not stored" in dependency.redactions


def test_sarif_import_cannot_escape_repository(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    outside = tmp_path / "outside.sarif"
    outside.write_text('{"version":"2.1.0","runs":[]}', encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(repository)
    plan = base.model_copy(
        update={
            "imports": (
                EvidenceImport(import_id="outside", path="../outside.sarif"),
            )
        }
    )
    result = service.run(plan, output_root=tmp_path / "artifacts")
    record = next(item for item in result.run.activities if item.activity_id == "import:outside")
    assert record.status.value == "failed"
    assert "must resolve inside" in record.message
    assert list((result.output_directory / "raw" / "sha256").iterdir()) == []


def test_sarif_can_be_hash_referenced_without_copying_raw(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    (repository / "empty.sarif").write_text(
        '{"version":"2.1.0","runs":[]}', encoding="utf-8"
    )
    service = EvidenceFrameworkService()
    base = service.create_default_plan(repository)
    plan = base.model_copy(
        update={
            "imports": (EvidenceImport(import_id="empty", path="empty.sarif"),),
            "sensitivity": SensitivityPolicy(raw_artifacts="referenced"),
        }
    )
    result = service.run(plan, output_root=tmp_path / "artifacts")
    assert list((result.output_directory / "raw" / "sha256").iterdir()) == []
    assert "repository references" in " ".join(service.preview(plan).reads)


def test_assessment_contract_rejects_broken_traceability(tmp_path: Path) -> None:
    repository = _repository(tmp_path / "repo")
    service = EvidenceFrameworkService()
    result = service.run(
        service.create_default_plan(repository), output_root=tmp_path / "artifacts"
    )
    payload = result.assessment.model_dump(mode="json")
    payload["findings"][0]["claim_id"] = "missing-claim"
    with pytest.raises(ValueError, match="unknown claim"):
        AssessmentResult.model_validate(payload)
