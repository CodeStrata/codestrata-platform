#!/usr/bin/env python3
"""Dogfood Phase 5.11 repository onboarding orchestration.

Runs onboarding against CodeStrata, Spring Petclinic (if present), and a
synthetic-multilang fixture using a mocked assess runner when live assess is
too heavy — and a dry validation+manifest path for each target root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aimf.application.assessment.service import AssessmentCommandResult  # noqa: E402
from aimf.application.onboarding import OnboardingApplicationService  # noqa: E402
from aimf.application.onboarding.validation import (  # noqa: E402
    validate_output_directory,
    validate_repository_source,
)
from aimf.config.settings import AimfSettings  # noqa: E402
from aimf.reporting.modernization_models import AssessmentMode  # noqa: E402

TARGETS = (
    ("codestrata", ROOT),
    ("spring-petclinic", ROOT / ".aimf" / "workspace" / "spring-petclinic"),
    ("synthetic-multilang", ROOT / "examples" / "sample-js-app"),
)


def _settings(tmp: Path, repo: Path) -> AimfSettings:
    return AimfSettings.model_validate(
        {
            "repository": {"path": str(repo)},
            "workspace": {"directory": str(tmp / "ws")},
            "static_analysis": {"enabled": False},
            "knowledge": {"directory": str(tmp / "knowledge")},
            "ai": {"bedrock": {}, "embedding_provider": "deterministic"},
        }
    )


def _fake(tmp: Path, name: str, *, languages: list[str], frameworks: list[str]):
    run_dir = tmp / "reports" / name / "dogfood-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    html = run_dir / "report.html"
    json_path = run_dir / "report.json"
    html.write_text("<html>dogfood</html>", encoding="utf-8")
    techs = [{"name": n, "category": "language"} for n in languages] + [
        {"name": n, "category": "framework"} for n in frameworks
    ]
    json_path.write_text(
        json.dumps({"schema_version": "1.2", "assessment": {"technologies": techs}}),
        encoding="utf-8",
    )
    return AssessmentCommandResult(
        repository_name=name,
        run_directory=run_dir,
        html_report_path=html,
        json_report_path=json_path,
        mode=AssessmentMode.DETERMINISTIC,
        findings_count=1,
        technologies_count=len(techs),
        recommendations_count=1,
        phases_count=0,
        ai_executed=False,
        rule_finding_count=1,
        phase3_recommendation_count=1,
        roadmap_report_initiative_count=1,
        knowledge_repository_id=f"repo:{name}",
        knowledge_run_id=f"run:{name}",
        knowledge_index_status="succeeded",
        knowledge_vector_count=3,
        knowledge_index_fingerprint=f"fp:{name}",
    )


def main() -> None:
    out_root = ROOT / "reports" / "dogfood-phase-5-11"
    validate_output_directory(out_root)
    summaries: dict[str, object] = {}
    profiles = {
        "codestrata": (["Python"], ["Typer"]),
        "spring-petclinic": (["Java"], ["Spring"]),
        "synthetic-multilang": (["JavaScript"], []),
    }
    for label, path in TARGETS:
        if not path.is_dir():
            summaries[label] = {"skipped": True, "reason": f"missing {path}"}
            print(f"{label}: skipped (missing {path})")
            continue
        validate_repository_source(str(path))
        langs, frames = profiles[label]

        def _make_runner(
            current_label: str, current_langs: list[str], current_frames: list[str]
        ):
            def _runner(**kwargs: object) -> AssessmentCommandResult:
                return _fake(
                    out_root,
                    current_label,
                    languages=current_langs,
                    frameworks=current_frames,
                )

            return _runner

        service = OnboardingApplicationService(
            assess_runner=_make_runner(label, langs, frames)
        )
        result = service.onboard(
            str(path),
            settings=_settings(out_root, path),
            output_directory=out_root / label,
            provider="deterministic",
        )
        second = service.onboard(
            str(path),
            settings=_settings(out_root, path),
            output_directory=out_root / f"{label}-repeat",
            provider="deterministic",
            force_reindex=True,
        )
        summaries[label] = {
            "status": result.status.value,
            "languages": list(result.summary.languages_detected),
            "frameworks": list(result.summary.frameworks_detected),
            "chunks_indexed": result.summary.chunks_indexed,
            "manifest": result.manifest_path,
            "repeatable_languages": list(second.summary.languages_detected),
            "force_reindex_ok": second.status.value == "succeeded",
        }
        print(
            f"{label}: status={result.status.value} "
            f"languages={result.summary.languages_detected} "
            f"chunks={result.summary.chunks_indexed}"
        )
    target = out_root / "summary.json"
    target.write_text(json.dumps(summaries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
