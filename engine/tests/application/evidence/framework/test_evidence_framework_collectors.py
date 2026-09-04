from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from codestrata.application.evidence.framework.collectors import (
    CollectorContext,
    CollectorRegistry,
    DependencyCollectorAdapter,
    FilePatternCollector,
    RepositoryInventoryCollector,
    repository_revision,
)
from codestrata.application.evidence.framework.service import EvidenceFrameworkService
from codestrata.domain.evidence.framework.models import EvidenceActivity


def test_registry_rejects_duplicate_collector_ids() -> None:
    with pytest.raises(ValueError, match="duplicate collector ID"):
        CollectorRegistry((RepositoryInventoryCollector(), RepositoryInventoryCollector()))


def test_repository_revision_ignores_codestrata_artifacts_only(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    tracked = tmp_path / "tracked.py"
    tracked.write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=CodeStrata Test",
            "-c",
            "user.email=test@codestrata.invalid",
            "commit",
            "-m",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    artifacts = tmp_path / ".codestrata-artifacts"
    artifacts.mkdir()
    (artifacts / "report.html").write_text("generated", encoding="utf-8")
    assert repository_revision(tmp_path) == head

    tracked.write_text("value = 2\n", encoding="utf-8")
    assert repository_revision(tmp_path) == f"{head}+dirty"


def test_inventory_detects_existing_meta_framework_configuration(tmp_path: Path) -> None:
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    plan = service.create_default_plan(tmp_path)
    activity = plan.activities[0]
    result = service.registry.get(activity.collector_id).collect(
        CollectorContext(plan=plan, activity=activity, repository=tmp_path, run_id="run")
    )
    payload = result.evidence[0].payload
    assert payload["languages"] == {"Python": 1}
    assert payload["quality_orchestration"] == (
        {"tool": "pre-commit", "configuration_path": ".pre-commit-config.yaml"},
    )
    assert payload["source_text_stored"] is False


def test_pattern_collector_records_locations_without_source_text(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("# TODO: replace this\nprint('ok')\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    activity = EvidenceActivity(
        activity_id="patterns",
        collector_id="codestrata.file-pattern",
        configuration={"patterns": [{"id": "todo", "regex": r"\bTODO\b", "globs": ["*.py"]}]},
    )
    plan = base.model_copy(update={"activities": (activity,)})
    result = FilePatternCollector().collect(
        CollectorContext(plan=plan, activity=activity, repository=tmp_path, run_id="run")
    )
    assert [item.kind for item in result.evidence] == [
        "source.pattern.search",
        "source.pattern.occurrence",
    ]
    occurrence = result.evidence[1]
    assert occurrence.locations[0].path == "main.py"
    assert occurrence.locations[0].start_line == 1
    assert "TODO" not in str(occurrence.payload)


def test_pattern_absence_has_explicit_complete_population(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    activity = EvidenceActivity(
        activity_id="patterns",
        collector_id="codestrata.file-pattern",
        configuration={"patterns": [{"id": "todo", "regex": "TODO", "globs": ["*.py"]}]},
    )
    plan = base.model_copy(update={"activities": (activity,)})
    result = FilePatternCollector().collect(
        CollectorContext(plan=plan, activity=activity, repository=tmp_path, run_id="run")
    )
    summary = result.evidence[0]
    assert summary.payload["assertion"] == "absent"
    assert summary.coverage.supports_absence_conclusion is True
    assert summary.coverage.population


def test_pattern_preview_rejects_invalid_regex(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('ok')\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    activity = EvidenceActivity(
        activity_id="patterns",
        collector_id="codestrata.file-pattern",
        configuration={"patterns": [{"id": "broken", "regex": "("}]},
    )
    plan = base.model_copy(update={"activities": (activity,)})
    with pytest.raises(ValueError, match="invalid regex"):
        service.preview(plan)


def test_pattern_evidence_is_bounded_by_plan_limit(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("TODO\nTODO\nTODO\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    activity = EvidenceActivity(
        activity_id="patterns",
        collector_id="codestrata.file-pattern",
        configuration={"patterns": [{"id": "todo", "regex": "TODO"}]},
    )
    plan = base.model_copy(
        update={
            "activities": (activity,),
            "limits": base.limits.model_copy(update={"max_evidence_records": 2}),
        }
    )
    result = FilePatternCollector().collect(
        CollectorContext(plan=plan, activity=activity, repository=tmp_path, run_id="run")
    )
    assert len(result.evidence) == 2
    assert result.coverage.state.value == "partial"
    assert result.evidence[0].payload["occurrence_count_is_lower_bound"] is True


def test_custom_pattern_run_creates_contextual_review_action(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("# TODO: explain\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    activity = EvidenceActivity(
        activity_id="patterns",
        collector_id="codestrata.file-pattern",
        configuration={"patterns": [{"id": "todo", "regex": "TODO", "globs": ["*.py"]}]},
    )
    plan = base.model_copy(update={"activities": (activity,)})
    result = service.run(plan, output_root=tmp_path / "artifacts")
    pattern_finding = next(
        item for item in result.assessment.findings if "Custom observation" in item.title
    )
    assert pattern_finding.locations[0].path == "main.py"
    action = next(
        item for item in result.assessment.actions if item.finding_id == pattern_finding.finding_id
    )
    assert action.title == "Review 1 location(s) for todo"


def test_unsupported_dependency_manifest_is_partial_not_empty_complete(
    tmp_path: Path,
) -> None:
    (tmp_path / "package.json").write_text('{"dependencies":{"react":"19.0.0"}}', encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    activity = next(
        item
        for item in base.activities
        if item.collector_id == "codestrata.dependency-declarations"
    )
    result = DependencyCollectorAdapter().collect(
        CollectorContext(plan=base, activity=activity, repository=tmp_path, run_id="run")
    )
    assert result.coverage.state.value == "partial"
    assert result.coverage.planned == 1
    assert result.coverage.examined == 0
    assert result.evidence[0].payload["unsupported_dependency_artifacts"] == ["package.json"]


def test_catalog_recommends_language_and_health_packs_for_python(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    catalog = service.catalog(tmp_path)

    assert catalog.detected_languages == ("python",)
    assert {item.collector_id for item in catalog.collectors} >= {
        "language.python.core",
        "codestrata.structural-health",
        "external.repowise-health",
    }
    recommended = {item.pack.pack_id for item in catalog.packs if item.status == "recommended"}
    assert {"repository-baseline", "language-intelligence", "code-health"} <= recommended


def test_language_pack_resolves_only_applicable_providers(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("from pathlib import Path\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    plan = service.apply_packs(
        base,
        ("repository-baseline@1.0", "language-intelligence@1.0"),
    )

    collector_ids = {item.collector_id for item in plan.activities}
    assert "language.python.core" in collector_ids
    assert "language.java.core" not in collector_ids
    assert plan.packs == (
        "repository-baseline@1.0",
        "language-intelligence@1.0",
    )
    assert not any(
        "Pack language-intelligence@1.0 is missing required collectors" in item
        for item in service.preview(plan).blind_spots
    )

    result = service.run(plan, output_root=tmp_path / "artifacts")
    summary = next(item for item in result.evidence if item.kind == "language.provider-summary")
    assert summary.payload["language"] == "python"
    assert any(item.kind == "language.source-unit" for item in result.evidence)


def test_selected_structural_biomarker_and_threshold_create_actionable_report(
    tmp_path: Path,
) -> None:
    source = """def risky(a, b, c):
    total = a + b
    if total:
        total += c
    return total
"""
    (tmp_path / "main.py").write_text(source, encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    plan = base.model_copy(
        update={
            "packs": ("code-health@1.0",),
            "activities": (
                EvidenceActivity(
                    activity_id="structural-health",
                    collector_id="codestrata.structural-health",
                    configuration={
                        "biomarkers": ["long_callable"],
                        "thresholds": {"long_callable": 3},
                    },
                ),
            ),
            "assessment_profile": "engineering-health-review@1.0",
        }
    )

    result = service.run(plan, output_root=tmp_path / "artifacts")
    biomarkers = [item for item in result.evidence if item.kind == "code-health.biomarker"]
    assert [item.payload["biomarker_id"] for item in biomarkers] == ["long_callable"]
    assert biomarkers[0].payload["threshold"] == 3
    assert any("Extract a named method" in item.title for item in result.assessment.actions)
    html = (result.output_directory / "report.html").read_text(encoding="utf-8")
    assert "Your evidence choices" in html
    assert "long_callable" in html
    assert "below 3" in html


def test_javascript_receives_honest_file_level_health_measurement(tmp_path: Path) -> None:
    (tmp_path / "app.ts").write_text("\n".join(["export const value = 1;"] * 8), encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    plan = base.model_copy(
        update={
            "packs": ("code-health@1.0",),
            "activities": (
                EvidenceActivity(
                    activity_id="structural-health",
                    collector_id="codestrata.structural-health",
                    configuration={
                        "biomarkers": ["large_file"],
                        "thresholds": {"large_file": 5},
                    },
                ),
            ),
            "assessment_profile": "engineering-health-review@1.0",
        }
    )

    result = service.run(plan, output_root=tmp_path / "artifacts")
    measurement = next(item for item in result.evidence if item.kind == "code-health.measurement")
    assert measurement.payload["language"] == "typescript"
    assert measurement.payload["metrics"]["physical_line_count"] == 8
    finding = next(item for item in result.evidence if item.kind == "code-health.biomarker")
    assert finding.payload["biomarker_id"] == "large_file"
    assert any(
        "Callable-level typed complexity" in item
        for item in service.registry.get("codestrata.structural-health").manifest.limitations
    )


def test_repowise_adapter_filters_selected_biomarkers_and_retains_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    native = {
        "kpis": {"average_health": 7.2},
        "metrics": [
            {
                "file_path": "main.py",
                "score": 7.2,
                "max_ccn": 12,
                "max_nesting": 5,
                "nloc": 80,
            }
        ],
        "findings": [
            {
                "biomarker_type": "complex_method",
                "severity": "high",
                "file_path": "main.py",
                "health_impact": 0.8,
                "reason": "Method complexity is elevated.",
                "details": {},
            },
            {
                "biomarker_type": "ownership_risk",
                "severity": "medium",
                "file_path": "main.py",
                "health_impact": 0.4,
                "reason": "Ownership is dispersed.",
                "details": {},
            },
        ],
    }
    monkeypatch.setattr(
        "codestrata.application.evidence.framework.collectors.shutil.which",
        lambda name: "/usr/local/bin/repowise" if name == "repowise" else None,
    )
    monkeypatch.setattr(
        "codestrata.application.evidence.framework.collectors.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=json.dumps(native),
            stderr="",
        ),
    )
    (tmp_path / "main.py").write_text("print('hello')\n", encoding="utf-8")
    service = EvidenceFrameworkService()
    base = service.create_default_plan(tmp_path)
    plan = base.model_copy(
        update={
            "packs": ("code-health@1.0",),
            "activities": (
                EvidenceActivity(
                    activity_id="repowise-health",
                    collector_id="external.repowise-health",
                    configuration={"biomarkers": ["complex_method"]},
                ),
            ),
            "assessment_profile": "engineering-health-review@1.0",
        }
    )

    result = service.run(plan, output_root=tmp_path / "artifacts")
    findings = [item for item in result.evidence if item.kind == "code-health.biomarker"]
    assert [item.payload["biomarker_id"] for item in findings] == ["complex_method"]
    assert findings[0].raw_references[0].sha256
    assert any(item.priority == "now" for item in result.assessment.actions)
