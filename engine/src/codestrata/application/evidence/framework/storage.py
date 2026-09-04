"""Portable, staged local artifact store for evidence runs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from codestrata.domain.evidence.framework.models import (
    AssessmentResult,
    EvidenceEnvelope,
    EvidencePlan,
    RawArtifactReference,
    RunRecord,
)


def _safe_segment(value: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_." else "-"
        for character in value
    )
    cleaned = cleaned.strip(".-")
    return cleaned or "repository"


class RunArtifactWorkspace:
    """Write a complete run in staging, then atomically expose it."""

    def __init__(self, output_root: Path, repository_id: str, run_id: str) -> None:
        repository_root = output_root / "evidence" / _safe_segment(repository_id)
        repository_root.mkdir(parents=True, exist_ok=True)
        repository_root.chmod(0o700)
        self.final_directory = repository_root / _safe_segment(run_id)
        self.staging_directory = repository_root / f".{_safe_segment(run_id)}.staging"
        if self.staging_directory.exists() or self.final_directory.exists():
            raise FileExistsError(f"run artifact path already exists for {run_id}")
        self.staging_directory.mkdir(parents=True)
        self.staging_directory.chmod(0o700)
        raw_directory = self.staging_directory / "raw" / "sha256"
        raw_directory.mkdir(parents=True)
        raw_directory.chmod(0o700)

    def store_raw(self, content: bytes, *, media_type: str) -> RawArtifactReference:
        digest = hashlib.sha256(content).hexdigest()
        relative = Path("raw") / "sha256" / digest
        destination = self.staging_directory / relative
        if not destination.exists():
            destination.write_bytes(content)
            destination.chmod(0o600)
        return RawArtifactReference(
            sha256=digest,
            media_type=media_type,
            relative_path=relative.as_posix(),
        )

    @staticmethod
    def reference_repository_raw(
        content: bytes,
        *,
        media_type: str,
        repository_relative_path: str,
    ) -> RawArtifactReference:
        return RawArtifactReference(
            sha256=hashlib.sha256(content).hexdigest(),
            media_type=media_type,
            relative_path=repository_relative_path,
            storage_mode="repository_referenced",
        )

    def write_contracts(
        self,
        *,
        plan: EvidencePlan,
        run: RunRecord,
        evidence: tuple[EvidenceEnvelope, ...],
        coverage: dict[str, Any],
        assessment: AssessmentResult,
        html_report: str,
        sarif_report: dict[str, Any],
    ) -> None:
        plan_payload = plan.model_dump(mode="json")
        (self.staging_directory / "plan.yaml").write_text(
            yaml.safe_dump(
                plan_payload,
                allow_unicode=True,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        (self.staging_directory / "plan.yaml").chmod(0o600)
        self._write_json("run.json", run.model_dump(mode="json"))
        with (self.staging_directory / "evidence.jsonl").open("w", encoding="utf-8") as handle:
            for item in evidence:
                handle.write(
                    json.dumps(
                        item.model_dump(mode="json"),
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    )
                )
                handle.write("\n")
        (self.staging_directory / "evidence.jsonl").chmod(0o600)
        self._write_json("coverage.json", coverage)
        self._write_json("assessment.json", assessment.model_dump(mode="json"))
        (self.staging_directory / "report.html").write_text(html_report, encoding="utf-8")
        (self.staging_directory / "report.html").chmod(0o600)
        self._write_json("report.sarif", sarif_report)

    def _write_json(self, name: str, payload: Any) -> None:
        destination = self.staging_directory / name
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        destination.chmod(0o600)

    def promote(self) -> Path:
        mandatory = {
            "plan.yaml",
            "run.json",
            "evidence.jsonl",
            "coverage.json",
            "assessment.json",
            "report.html",
            "report.sarif",
        }
        missing = sorted(
            name for name in mandatory if not (self.staging_directory / name).is_file()
        )
        if missing:
            raise ValueError(f"run staging is missing mandatory artifacts: {missing}")
        self.staging_directory.replace(self.final_directory)
        return self.final_directory
