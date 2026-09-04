"""End-to-end evidence planning, execution, assessment, and reporting service."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

from codestrata.application.evidence.framework.assessment import (
    AssessmentProfileRegistry,
    assess_evidence,
    create_default_profile_registry,
)
from codestrata.application.evidence.framework.catalog import (
    EvidencePackRegistry,
    build_catalog,
)
from codestrata.application.evidence.framework.collectors import (
    CollectionResult,
    CollectorContext,
    CollectorRegistry,
    create_default_registry,
    repository_revision,
)
from codestrata.application.evidence.framework.sarif import normalize_sarif_document
from codestrata.application.evidence.framework.storage import RunArtifactWorkspace
from codestrata.domain.evidence.framework.identifiers import stable_id
from codestrata.domain.evidence.framework.models import (
    ActivityRecord,
    ActivityStatus,
    AssessmentResult,
    CollectorPreview,
    Coverage,
    CoverageState,
    EvidenceActivity,
    EvidenceCatalog,
    EvidenceEnvelope,
    EvidencePlan,
    ExecutionEvent,
    PlanPreview,
    RepositorySubject,
    RunRecord,
    RunStatus,
)
from codestrata.reporting.evidence_framework import render_html, render_sarif
from codestrata.security.redaction import redact_secrets

EventCallback = Callable[[ExecutionEvent], None]


@dataclass(frozen=True)
class EvidenceRunResult:
    plan: EvidencePlan
    run: RunRecord
    assessment: AssessmentResult
    evidence: tuple[EvidenceEnvelope, ...]
    output_directory: Path
    events: tuple[ExecutionEvent, ...]


class EvidenceFrameworkService:
    """The use-case boundary shared by CLI and local studio."""

    def __init__(
        self,
        registry: CollectorRegistry | None = None,
        profile_registry: AssessmentProfileRegistry | None = None,
        pack_registry: EvidencePackRegistry | None = None,
    ) -> None:
        self.registry = registry or create_default_registry()
        self.profile_registry = profile_registry or create_default_profile_registry()
        self.pack_registry = pack_registry or EvidencePackRegistry()

    def catalog(self, repository: Path) -> EvidenceCatalog:
        return build_catalog(
            repository.expanduser().resolve(),
            registry=self.registry,
            packs=self.pack_registry,
        )

    def apply_packs(self, plan: EvidencePlan, selections: tuple[str, ...]) -> EvidencePlan:
        return self.pack_registry.apply(
            plan,
            selections=selections,
            registry=self.registry,
            repository=Path(plan.subject.path).expanduser().resolve(),
        )

    def create_default_plan(
        self,
        repository: Path,
        *,
        goal: str = "Understand the repository evidence available for an engineering decision",
        questions: tuple[str, ...] = (
            "What is present in the repository?",
            "What dependency and testing evidence is observable?",
            "Where is evidence incomplete or inconclusive?",
        ),
    ) -> EvidencePlan:
        root = repository.expanduser().resolve()
        revision = repository_revision(root)
        repository_id = root.name or "repository"
        return EvidencePlan(
            plan_id=stable_id("plan", repository_id, revision, goal),
            goal=goal,
            questions=questions,
            subject=RepositorySubject(
                repository_id=repository_id,
                path=str(root),
                revision=revision,
            ),
            packs=("repository-baseline@1.0",),
            activities=(
                EvidenceActivity(
                    activity_id="inventory",
                    collector_id="codestrata.repository-inventory",
                ),
                EvidenceActivity(
                    activity_id="dependencies",
                    collector_id="codestrata.dependency-declarations",
                ),
                EvidenceActivity(
                    activity_id="testing",
                    collector_id="codestrata.testing-structure",
                ),
            ),
        )

    @staticmethod
    def load_plan(path: Path) -> EvidencePlan:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise ValueError(f"could not load evidence plan {path}: {error}") from error
        if not isinstance(payload, dict):
            raise ValueError("evidence plan root must be an object")
        return EvidencePlan.model_validate(payload)

    @staticmethod
    def save_plan(plan: EvidencePlan, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                plan.model_dump(mode="json"),
                allow_unicode=True,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        path.chmod(0o600)
        return path

    def preview(self, plan: EvidencePlan) -> PlanPreview:
        repository = Path(plan.subject.path).expanduser().resolve()
        selected_packs = self.pack_registry.expand(plan.packs)
        manifests = {item.collector_id: item for item in self.registry.manifests()}
        self.profile_registry.resolve(
            plan.assessment_profile,
            plan=plan,
            collectors=manifests,
        )
        rows: list[CollectorPreview] = []
        reads = [f"Repository files under {repository}"]
        executes: list[str] = []
        leaves_machine: list[str] = []
        blind_spots: list[str] = []
        selected_collector_ids = {item.collector_id for item in plan.activities if item.enabled}
        for pack in selected_packs:
            missing_required = [
                item.collector_id
                for item in pack.activities
                if item.required and item.collector_id not in selected_collector_ids
            ]
            if missing_required:
                blind_spots.append(
                    f"Pack {pack.key} is missing required collectors: "
                    f"{', '.join(missing_required)}."
                )
            blind_spots.extend(pack.limitations)
        for activity in plan.activities:
            if not activity.enabled:
                continue
            try:
                collector = self.registry.get(activity.collector_id)
            except KeyError:
                raise ValueError(
                    f"activities.{activity.activity_id}.collector_id: "
                    f"unknown collector {activity.collector_id!r}"
                ) from None
            context = CollectorContext(
                plan=plan,
                activity=activity,
                repository=repository,
                run_id="preview",
            )
            available, availability_reason = collector.available()
            applicable, applicability_reason = collector.applicable(context)
            status: Literal["applicable", "inapplicable", "unavailable", "blocked"]
            if not available:
                status = "unavailable"
                reason = availability_reason
            elif (
                collector.manifest.external_access.value != "none"
                and plan.limits.external_access == "deny"
            ):
                status = "blocked"
                reason = "Plan denies external access."
            elif not applicable:
                status = "inapplicable"
                reason = applicability_reason
            else:
                status = "applicable"
                reason = applicability_reason
            rows.append(
                CollectorPreview(
                    activity_id=activity.activity_id,
                    collector_id=activity.collector_id,
                    status=status,
                    reason=reason,
                    manifest=collector.manifest,
                )
            )
            if collector.manifest.runs_code:
                executes.append(f"{collector.manifest.label} local executable")
            if collector.manifest.external_access.value != "none":
                leaves_machine.append(
                    f"{collector.manifest.label}: network behavior depends on tool configuration"
                )
            blind_spots.extend(collector.manifest.limitations)
        if not leaves_machine:
            leaves_machine.append("Nothing; every selected activity is local-only.")
        if plan.imports:
            reads.extend(f"Imported artifact {item.path}" for item in plan.imports)
            if plan.sensitivity.raw_artifacts == "copied":
                reads.append(
                    "Imported raw artifacts are copied into the local content-addressed store"
                )
            else:
                reads.append(
                    "Imported raw artifacts remain repository references; hashes are recorded"
                )
        return PlanPreview(
            plan_id=plan.plan_id,
            collectors=tuple(rows),
            reads=tuple(reads),
            executes=tuple(executes),
            leaves_machine=tuple(leaves_machine),
            blind_spots=tuple(dict.fromkeys(blind_spots)),
        )

    def run(
        self,
        plan: EvidencePlan,
        *,
        output_root: Path = Path(".codestrata-artifacts"),
        on_event: EventCallback | None = None,
        cancel: threading.Event | None = None,
    ) -> EvidenceRunResult:
        repository = Path(plan.subject.path).expanduser().resolve()
        if not repository.is_dir():
            raise ValueError(f"repository does not exist or is not a directory: {repository}")
        actual_revision = repository_revision(repository)
        if actual_revision != plan.subject.revision:
            plan = plan.model_copy(
                update={"subject": plan.subject.model_copy(update={"revision": actual_revision})}
            )
        started_at = datetime.now(UTC)
        run_suffix = stable_id("run", plan.plan_id, actual_revision, started_at.isoformat()).split(
            ":"
        )[1][:8]
        run_id = f"{started_at.strftime('%Y%m%dT%H%M%SZ')}-{run_suffix}"
        workspace = RunArtifactWorkspace(
            output_root.expanduser().resolve(),
            plan.subject.repository_id,
            run_id,
        )
        events: list[ExecutionEvent] = []
        records: list[ActivityRecord] = []
        all_evidence: list[EvidenceEnvelope] = []
        coverage_payload: dict[str, Any] = {"schema_version": "1.0", "activities": {}}
        errors: list[str] = []

        def emit(activity_id: str, status: ActivityStatus, message: str) -> None:
            event = ExecutionEvent(
                run_id=run_id,
                sequence=len(events),
                activity_id=activity_id,
                status=status,
                message=message,
                occurred_at=datetime.now(UTC),
            )
            events.append(event)
            if on_event:
                on_event(event)

        preview = self.preview(plan)
        preview_by_id = {item.activity_id: item for item in preview.collectors}
        cancelled = False
        for activity in plan.activities:
            if not activity.enabled:
                continue
            if cancel is not None and cancel.is_set():
                cancelled = True
                emit(activity.activity_id, ActivityStatus.CANCELLED, "Run cancelled.")
                records.append(
                    ActivityRecord(
                        activity_id=activity.activity_id,
                        collector_id=activity.collector_id,
                        status=ActivityStatus.CANCELLED,
                        message="Run cancelled before activity started.",
                    )
                )
                continue
            row = preview_by_id[activity.activity_id]
            if row.status in {"blocked", "unavailable"}:
                status = ActivityStatus.BLOCKED
                emit(activity.activity_id, status, row.reason)
                records.append(
                    ActivityRecord(
                        activity_id=activity.activity_id,
                        collector_id=activity.collector_id,
                        status=status,
                        message=row.reason,
                    )
                )
                errors.append(f"{activity.activity_id}: {row.reason}")
                coverage_payload["activities"][activity.activity_id] = {
                    "state": "failed",
                    "message": row.reason,
                }
                continue
            if row.status == "inapplicable":
                emit(activity.activity_id, ActivityStatus.SKIPPED, row.reason)
                records.append(
                    ActivityRecord(
                        activity_id=activity.activity_id,
                        collector_id=activity.collector_id,
                        status=ActivityStatus.SKIPPED,
                        message=row.reason,
                    )
                )
                coverage_payload["activities"][activity.activity_id] = {
                    "state": "not_applicable",
                    "message": row.reason,
                }
                continue
            collector = self.registry.get(activity.collector_id)
            activity_started = datetime.now(UTC)
            emit(activity.activity_id, ActivityStatus.RUNNING, "Collection started.")
            try:
                result = collector.collect(
                    CollectorContext(
                        plan=plan,
                        activity=activity,
                        repository=repository,
                        run_id=run_id,
                    )
                )
                raw_references = tuple(
                    workspace.store_raw(
                        raw_artifact.content,
                        media_type=raw_artifact.media_type,
                    )
                    for raw_artifact in result.raw_artifacts
                )
                collected_evidence = tuple(
                    evidence.model_copy(
                        update={
                            "raw_references": (
                                *evidence.raw_references,
                                *raw_references,
                            )
                        }
                    )
                    for evidence in result.evidence
                )
                all_evidence.extend(collected_evidence)
                status = ActivityStatus.COMPLETED
                message = f"Collected {len(collected_evidence)} normalized evidence record(s)."
                coverage_payload["activities"][activity.activity_id] = {
                    **result.coverage.model_dump(mode="json"),
                    "diagnostics": list(result.diagnostics),
                }
            except Exception as error:  # noqa: BLE001 - activity isolation is deliberate
                safe_error = redact_secrets(str(error))
                result = CollectionResult(
                    evidence=(),
                    coverage=Coverage(
                        state=CoverageState.FAILED,
                        population="Planned collector population.",
                        successful=False,
                        limitations=(safe_error,),
                    ),
                )
                collected_evidence = ()
                status = ActivityStatus.FAILED
                message = f"Collection failed: {safe_error}"
                errors.append(f"{activity.activity_id}: {safe_error}")
                coverage_payload["activities"][activity.activity_id] = result.coverage.model_dump(
                    mode="json"
                )
            finished = datetime.now(UTC)
            records.append(
                ActivityRecord(
                    activity_id=activity.activity_id,
                    collector_id=activity.collector_id,
                    status=status,
                    evidence_count=len(collected_evidence),
                    started_at=activity_started,
                    finished_at=finished,
                    message=message,
                )
            )
            emit(activity.activity_id, status, message)

        for item in plan.imports:
            activity_id = f"import:{item.import_id}"
            started = datetime.now(UTC)
            emit(activity_id, ActivityStatus.RUNNING, f"Importing {item.path}.")
            try:
                source = Path(item.path).expanduser()
                if not source.is_absolute():
                    source = repository / source
                source = source.resolve(strict=True)
                if not source.is_relative_to(repository):
                    raise ValueError("import path must resolve inside the selected repository")
                content = source.read_bytes()
                if plan.sensitivity.raw_artifacts == "copied":
                    raw_reference = workspace.store_raw(
                        content,
                        media_type="application/sarif+json",
                    )
                else:
                    raw_reference = workspace.reference_repository_raw(
                        content,
                        media_type="application/sarif+json",
                        repository_relative_path=source.relative_to(repository).as_posix(),
                    )
                document = json.loads(content)
                import_activity = EvidenceActivity(
                    activity_id=activity_id,
                    collector_id="import.sarif",
                )
                imported, imported_coverage = normalize_sarif_document(
                    document=document,
                    context=CollectorContext(
                        plan=plan,
                        activity=import_activity,
                        repository=repository,
                        run_id=run_id,
                    ),
                    raw_reference=raw_reference,
                )
                all_evidence.extend(imported)
                status = ActivityStatus.COMPLETED
                message = f"Imported {len(imported)} SARIF result(s)."
                coverage_payload["activities"][activity_id] = imported_coverage.model_dump(
                    mode="json"
                )
            except Exception as error:  # noqa: BLE001 - imports are isolated activities
                status = ActivityStatus.FAILED
                safe_error = redact_secrets(str(error))
                message = f"Import failed: {safe_error}"
                errors.append(f"{activity_id}: {safe_error}")
                imported = ()
                coverage_payload["activities"][activity_id] = {
                    "state": "failed",
                    "message": safe_error,
                }
            records.append(
                ActivityRecord(
                    activity_id=activity_id,
                    collector_id="import.sarif",
                    status=status,
                    evidence_count=len(imported),
                    started_at=started,
                    finished_at=datetime.now(UTC),
                    message=message,
                )
            )
            emit(activity_id, status, message)

        for attestation in plan.attestations:
            activity_id = f"attestation:{attestation.attestation_id}"
            coverage = Coverage(
                state=CoverageState.COMPLETE,
                population="The declaration supplied in the evidence plan.",
                planned=1,
                examined=1,
                successful=True,
            )
            attestation_payload = {
                "attestation_id": attestation.attestation_id,
                "statement": attestation.statement,
                "source": attestation.source,
            }
            if plan.sensitivity.redact_secrets:
                attestation_payload = {
                    key: redact_secrets(value) for key, value in attestation_payload.items()
                }
            declaration = EvidenceEnvelope.create(
                kind="manual.attestation",
                run_id=run_id,
                activity_id=activity_id,
                collector_id="manual.attestation",
                collector_version="1.0.0",
                repository_id=plan.subject.repository_id,
                revision=plan.subject.revision,
                method="user declaration",
                production_mode="declared",
                coverage=coverage,
                payload=attestation_payload,
                confidence_basis=attestation.confidence_basis,
            )
            all_evidence.append(declaration)
            message = "Recorded declared evidence; not independently verified."
            records.append(
                ActivityRecord(
                    activity_id=activity_id,
                    collector_id="manual.attestation",
                    status=ActivityStatus.COMPLETED,
                    evidence_count=1,
                    started_at=datetime.now(UTC),
                    finished_at=datetime.now(UTC),
                    message=message,
                )
            )
            coverage_payload["activities"][activity_id] = coverage.model_dump(mode="json")
            emit(activity_id, ActivityStatus.COMPLETED, message)

        evidence_ids = {item.evidence_id for item in all_evidence}
        missing_parents = sorted(
            parent
            for item in all_evidence
            for parent in item.parent_evidence_ids
            if parent not in evidence_ids
        )
        if missing_parents:
            raise ValueError(f"derived evidence references missing parents: {missing_parents}")

        manifests = {item.collector_id: item for item in self.registry.manifests()}
        profile = self.profile_registry.resolve(
            plan.assessment_profile,
            plan=plan,
            collectors=manifests,
        )
        assessment = assess_evidence(
            plan=plan,
            run_id=run_id,
            profile=profile,
            activity_records=tuple(records),
            evidence=tuple(all_evidence),
        )
        if cancelled:
            run_status = RunStatus.CANCELLED
        elif any(
            item.status in {ActivityStatus.FAILED, ActivityStatus.BLOCKED} for item in records
        ):
            run_status = RunStatus.PARTIAL
        else:
            run_status = RunStatus.COMPLETED
        run = RunRecord(
            run_id=run_id,
            plan_id=plan.plan_id,
            status=run_status,
            repository_id=plan.subject.repository_id,
            revision=plan.subject.revision,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            activities=tuple(records),
            errors=tuple(errors),
        )
        html = render_html(
            plan=plan,
            run=run,
            assessment=assessment,
            evidence=tuple(all_evidence),
        )
        sarif = render_sarif(assessment)
        workspace.write_contracts(
            plan=plan,
            run=run,
            evidence=tuple(all_evidence),
            coverage=coverage_payload,
            assessment=assessment,
            html_report=html,
            sarif_report=sarif,
        )
        output_directory = workspace.promote()
        return EvidenceRunResult(
            plan=plan,
            run=run,
            assessment=assessment,
            evidence=tuple(all_evidence),
            output_directory=output_directory,
            events=tuple(events),
        )
