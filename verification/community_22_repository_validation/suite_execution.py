"""Full 22-repository suite execution for Slice 17.13.

Clones outside the monorepo (git config isolated), assesses into
``.codestrata-artifacts/assessments/``, and records per-repo results.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import venv
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.catalog import CatalogRepository
from verification.community_22_repository_validation.contract import (
    ASSESSMENTS_RELATIVE,
    SUITE_ID,
    VALIDATION_LOGS_RELATIVE,
    VALIDATION_REPOSITORIES_RELATIVE,
)
from verification.community_22_repository_validation.repository_runner import (
    clone_repository,
    git_isolation_env,
)

# Tier timeouts aligned with SV.10 / curated_repository_validation.
_ASSESS_TIMEOUT_S = {
    "tier1": 5 * 60,
    "tier2": 15 * 60,
    "tier3": 20 * 60,
    "tier4": 30 * 60,
}
_CLONE_TIMEOUT_S = {
    "tier1": 5 * 60,
    "tier2": 10 * 60,
    "tier3": 15 * 60,
    "tier4": 30 * 60,
}


@dataclass
class ExecutedRepositoryResult:
    repository_validation_id: str
    language: str | None
    ecosystem: str | None
    tier: str
    qualified_revision: str
    clone_status: str
    assessment_status: str
    report_status: str
    head_status_summary: str
    eir_eligible: bool
    telemetry_status: str
    defect_count: int
    limitations: list[str] = field(default_factory=list)
    assessment_run_id: str | None = None
    assessment_artifact_ref: str | None = None
    duration_seconds: float | None = None
    exit_code: int | None = None
    quality_class: str | None = None
    detail: str = ""

    def to_register_entry(self) -> dict[str, Any]:
        return {
            "repository_validation_id": self.repository_validation_id,
            "language": self.language,
            "ecosystem": self.ecosystem,
            "assessment_status": self.assessment_status,
            "head_status_summary": self.head_status_summary,
            "report_status": self.report_status,
            "eir_eligible": self.eir_eligible,
            "telemetry_status": self.telemetry_status,
            "defect_count": self.defect_count,
            "limitations": list(self.limitations),
            "assessment_run_id": self.assessment_run_id,
            "assessment_artifact_ref": self.assessment_artifact_ref,
            "quality_class": self.quality_class,
            "tier": self.tier,
        }


def _tier_for(repo: CatalogRepository) -> str:
    raw = repo.raw.get("expected_runtime_tier") or repo.raw.get("tier") or "tier3"
    return str(raw)


def _ensure_engine_path(monorepo: Path) -> None:
    import sys

    engine = str((monorepo / "engine").resolve())
    if engine not in sys.path:
        sys.path.append(engine)
    import verification as verification_pkg
    from pkgutil import extend_path

    verification_pkg.__path__ = extend_path(
        list(verification_pkg.__path__), verification_pkg.__name__
    )


def _install_cli(engine_root: Path, venv_dir: Path) -> Path:
    if not (venv_dir / "bin").exists() and not (venv_dir / "Scripts").exists():
        venv.create(venv_dir, with_pip=True, clear=False)
    python = venv_dir / "bin" / "python"
    if not python.is_file():
        python = venv_dir / "Scripts" / "python.exe"
    env = {**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1"}
    import subprocess

    subprocess.run(
        [str(python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )
    proc = subprocess.run(
        [str(python), "-m", "pip", "install", str(engine_root)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=600,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "")[-500:]
        raise RuntimeError(f"codestrata install failed: {detail}")
    codestrata = venv_dir / "bin" / "codestrata"
    if not codestrata.is_file():
        codestrata = venv_dir / "Scripts" / "codestrata.exe"
    if not codestrata.is_file():
        raise RuntimeError("codestrata executable missing after install")
    return codestrata


def _assessment_env(*, home: Path, venv_dir: Path, telemetry_endpoint: str | None) -> dict[str, str]:
    _ensure_engine_path(Path(__file__).resolve().parents[2])
    from verification.cli_installation.environment import with_venv_path
    from verification.repository_assessment.commands import assessment_environ

    env = assessment_environ(offline=False)
    env = with_venv_path(env, venv_dir)
    env["HOME"] = str(home)
    env["XDG_CONFIG_HOME"] = str(home / ".config")
    env["XDG_CACHE_HOME"] = str(home / ".cache")
    (home / ".config").mkdir(parents=True, exist_ok=True)
    (home / ".cache").mkdir(parents=True, exist_ok=True)
    # Synthetic validation installation home (not a Community end-user install).
    env["CODESTRATA_HOME"] = str(home / ".codestrata-validation")
    Path(env["CODESTRATA_HOME"]).mkdir(parents=True, exist_ok=True)
    # Never force-disable telemetry for this owner validation suite.
    env.pop("CODESTRATA_TELEMETRY", None)
    if telemetry_endpoint:
        env["CODESTRATA_TELEMETRY_ENDPOINT"] = telemetry_endpoint
    env.update(git_isolation_env())
    return env


def _find_new_run(assessments_root: Path, *, before: set[str], slug_hint: str) -> Path | None:
    if not assessments_root.is_dir():
        return None
    slug = slug_hint.strip().lower().replace("/", "-")
    prefix = f"{slug}-"
    candidates: list[Path] = []
    for child in assessments_root.iterdir():
        if not child.is_dir() or child.name in before:
            continue
        if not child.name.startswith(prefix):
            continue
        if (child / "assessment.json").is_file() and (child / "assessment.html").is_file():
            candidates.append(child)
    if not candidates:
        return None
    return sorted(candidates, key=lambda p: p.name, reverse=True)[0]


def _validate_run_artifacts(run_dir: Path) -> tuple[str, str, list[str]]:
    """Return (assessment_status, head_summary, limitations)."""

    limitations: list[str] = []
    manifest = run_dir / "assessment.json"
    html = run_dir / "assessment.html"
    heads = run_dir / "heads"
    if not manifest.is_file() or not html.is_file():
        return "incomplete", "missing_core", ["missing_assessment_json_or_html"]

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "defect", "manifest_corrupt", ["assessment_json_unparseable"]

    if not isinstance(data, dict):
        return "defect", "manifest_invalid", ["assessment_json_not_object"]

    # Absolute path / secret leak soft checks (manifest only).
    blob = json.dumps(data, sort_keys=True)
    if "/Users/" in blob or "/home/" in blob or "/var/folders/" in blob:
        limitations.append("absolute_path_in_manifest")
    if "AKIA" in blob or "cscc_v1_" in blob:
        return "defect", "secret_leak", ["secret_like_token_in_manifest"]

    completed = data.get("completed_heads") or data.get("head_references") or []
    head_files = list(heads.glob("*.json")) if heads.is_dir() else []
    head_summary = f"heads={len(head_files)};manifest_refs={len(completed)}"
    if heads.is_dir() and not head_files:
        limitations.append("heads_directory_empty")
    for path in head_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return "defect", head_summary, [f"head_corrupt:{path.name}"]

    # Legacy path references must not appear.
    html_text = html.read_text(encoding="utf-8", errors="replace")
    if "engine/reports" in html_text or "reports/verification" in html_text:
        limitations.append("legacy_report_path_in_html")
    if "undefined" in html_text.lower() and "undefined" in html_text:
        # Heuristic only — do not hard-fail solely on the substring in code samples.
        pass

    status = "pass" if not any(x.startswith("secret") for x in limitations) else "defect"
    if "absolute_path_in_manifest" in limitations:
        status = "pass_with_limitations"
    return status, head_summary, limitations


def _run_customer_workflow(
    codestrata: Path,
    *,
    repo_cwd: Path,
    env: dict[str, str],
    output_abs: Path,
    assess_timeout_s: float,
    telemetry_allow: bool,
) -> dict[str, Any]:
    _ensure_engine_path(Path(__file__).resolve().parents[2])
    from verification.repository_assessment.commands import run_codestrata, run_doctor, run_init

    doctor = run_doctor(codestrata, cwd=repo_cwd, env=env)
    if doctor.has_traceback:
        return {"stage": "doctor", "doctor": doctor, "init": None, "assess": None}

    init = run_init(codestrata, cwd=repo_cwd, env=env)
    if init.exit_code != 0 or init.has_traceback:
        return {"stage": "init", "doctor": doctor, "init": init, "assess": None}
    if not (repo_cwd / "codestrata.toml").is_file():
        return {"stage": "init_config_missing", "doctor": doctor, "init": init, "assess": None}

    doctor_post = run_doctor(codestrata, cwd=repo_cwd, env=env)
    if doctor_post.has_traceback:
        return {"stage": "doctor", "doctor": doctor_post, "init": init, "assess": None}

    args = [
        "assess",
        "--repo",
        ".",
        "--output",
        str(output_abs),
        "--no-ai",
        "--json-summary",
    ]
    if telemetry_allow:
        args.append("--telemetry-allow")
    assess = run_codestrata(
        codestrata,
        args,
        cwd=repo_cwd,
        env=env,
        name="assess",
        timeout_s=assess_timeout_s,
    )
    return {
        "stage": "assess",
        "doctor": doctor_post,
        "init": init,
        "assess": assess,
    }


def execute_one_repository(
    monorepo: Path,
    repo: CatalogRepository,
    *,
    codestrata: Path,
    venv_dir: Path,
    clone_root: Path,
    telemetry_endpoint: str | None = None,
    telemetry_allow: bool = True,
    keep_clone: bool = False,
) -> ExecutedRepositoryResult:
    tier = _tier_for(repo)
    limitations: list[str] = []
    if repo.requires_submodules:
        limitations.append("catalog declares submodules; assessed without initializing submodules")
    if repo.requires_git_lfs:
        limitations.append("catalog declares Git LFS; LFS objects were not fetched")

    result = ExecutedRepositoryResult(
        repository_validation_id=repo.repository_id,
        language=repo.language_group,
        ecosystem=repo.ecosystem,
        tier=tier,
        qualified_revision=repo.qualified_revision_value,
        clone_status="not_attempted",
        assessment_status="not_attempted",
        report_status="not_attempted",
        head_status_summary="not_attempted",
        eir_eligible=bool(repo.enabled_for.get("engineering_intelligence")),
        telemetry_status="attempted" if telemetry_allow else "disabled",
        defect_count=0,
        limitations=list(limitations),
    )

    workspace = Path(tempfile.mkdtemp(prefix=f"cs-sv1713-{repo.repository_id}-", dir=str(clone_root)))
    clone_dir = workspace / repo.repository_id
    home_dir = workspace / "home"
    home_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    assessments_root = monorepo / ASSESSMENTS_RELATIVE
    assessments_root.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in assessments_root.iterdir()} if assessments_root.is_dir() else set()

    log_dir = monorepo / VALIDATION_LOGS_RELATIVE
    log_dir.mkdir(parents=True, exist_ok=True)
    repo_meta_dir = monorepo / VALIDATION_REPOSITORIES_RELATIVE / repo.repository_id
    repo_meta_dir.mkdir(parents=True, exist_ok=True)

    try:
        ok, detail = clone_repository(
            monorepo,
            repo,
            clone_dir,
            timeout_s=int(_CLONE_TIMEOUT_S.get(tier, 900)),
        )
        result.clone_status = "pass" if ok else "fail"
        result.detail = detail
        if not ok:
            result.assessment_status = "clone_failed"
            result.report_status = "not_executed"
            result.head_status_summary = "not_executed"
            result.defect_count = 1
            result.quality_class = "UNSUPPORTED" if "forbidden" in detail else "DEFECT"
            result.limitations.append(f"clone_failed:{detail[:120]}")
            return result

        env = _assessment_env(home=home_dir, venv_dir=venv_dir, telemetry_endpoint=telemetry_endpoint)
        workflow = _run_customer_workflow(
            codestrata,
            repo_cwd=clone_dir,
            env=env,
            output_abs=assessments_root.resolve(),
            assess_timeout_s=float(_ASSESS_TIMEOUT_S.get(tier, 1200)),
            telemetry_allow=telemetry_allow,
        )
        stage = workflow.get("stage")
        assess = workflow.get("assess")
        if stage != "assess" or assess is None:
            result.assessment_status = "initialization_failure"
            result.report_status = "not_executed"
            result.head_status_summary = "not_executed"
            result.defect_count = 1
            result.quality_class = "DEFECT"
            result.exit_code = getattr(workflow.get(stage), "exit_code", None)
            result.limitations.append(f"stage_failed:{stage}")
            return result

        result.exit_code = assess.exit_code
        result.duration_seconds = round(float(assess.duration_seconds), 3)
        # Persist sanitized command log (no secrets).
        (log_dir / f"{repo.repository_id}.json").write_text(
            json.dumps(
                {
                    "repository_validation_id": repo.repository_id,
                    "exit_code": assess.exit_code,
                    "duration_bucket": assess.duration_bucket,
                    "stage": stage,
                    "stdout_sanitized": assess.stdout_sanitized[:1500],
                    "stderr_sanitized": assess.stderr_sanitized[:1500],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        run_dir = _find_new_run(assessments_root, before=before, slug_hint=repo.repository_id)
        if run_dir is None:
            result.assessment_status = "artifact_missing"
            result.report_status = "missing"
            result.head_status_summary = "missing"
            result.defect_count = 1
            result.quality_class = "DEFECT"
            result.limitations.append("assessment_run_directory_not_found_for_slug")
            return result

        result.assessment_run_id = run_dir.name
        result.assessment_artifact_ref = f"{ASSESSMENTS_RELATIVE}/{run_dir.name}"
        status, head_summary, art_limits = _validate_run_artifacts(run_dir)
        result.head_status_summary = head_summary
        result.limitations.extend(art_limits)
        result.report_status = "pass" if (run_dir / "assessment.html").is_file() else "fail"

        if assess.exit_code != 0:
            result.assessment_status = "assessment_failure"
            result.defect_count = 1
            result.quality_class = "DEFECT"
            result.limitations.append(f"assess_exit_{assess.exit_code}")
        elif status in {"pass", "pass_with_limitations"}:
            result.assessment_status = "pass"
            result.quality_class = "PASS" if status == "pass" else "PASS_WITH_LIMITATIONS"
        else:
            result.assessment_status = status
            result.defect_count = 1
            result.quality_class = "DEFECT"

        # Relative pointer only (no absolute path) for suite register.
        (repo_meta_dir / "result.json").write_text(
            json.dumps(result.to_register_entry(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return result
    finally:
        result.duration_seconds = result.duration_seconds or round(time.perf_counter() - started, 3)
        if not keep_clone:
            shutil.rmtree(workspace, ignore_errors=True)


def load_executed_results(
    monorepo: Path,
    repositories: tuple[CatalogRepository, ...],
) -> list[dict[str, Any]]:
    """Load register-safe results from validation/repositories or progress.jsonl."""

    by_id: dict[str, dict[str, Any]] = {}
    repos_root = monorepo / VALIDATION_REPOSITORIES_RELATIVE
    if repos_root.is_dir():
        for repo in repositories:
            path = repos_root / repo.repository_id / "result.json"
            if path.is_file():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if isinstance(data, dict):
                    by_id[repo.repository_id] = data

    progress = (
        monorepo
        / ".codestrata-artifacts/validation/suites"
        / SUITE_ID
        / "progress.jsonl"
    )
    if progress.is_file():
        for line in progress.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = str(row.get("repository_validation_id") or "")
            if rid:
                by_id[rid] = {
                    "repository_validation_id": rid,
                    "language": row.get("language"),
                    "ecosystem": row.get("ecosystem"),
                    "assessment_status": row.get("assessment_status"),
                    "head_status_summary": row.get("head_status_summary"),
                    "report_status": row.get("report_status"),
                    "eir_eligible": row.get("eir_eligible"),
                    "telemetry_status": row.get("telemetry_status"),
                    "defect_count": row.get("defect_count") or 0,
                    "limitations": row.get("limitations") or [],
                    "assessment_run_id": row.get("assessment_run_id"),
                    "assessment_artifact_ref": row.get("assessment_artifact_ref"),
                    "quality_class": row.get("quality_class"),
                }

    ordered: list[dict[str, Any]] = []
    for repo in repositories:
        if repo.repository_id in by_id:
            ordered.append(by_id[repo.repository_id])
        else:
            ordered.append(
                {
                    "repository_validation_id": repo.repository_id,
                    "language": repo.language_group,
                    "ecosystem": repo.ecosystem,
                    "assessment_status": "not_executed",
                    "head_status_summary": "not_executed",
                    "report_status": "not_executed",
                    "eir_eligible": bool(repo.enabled_for.get("engineering_intelligence")),
                    "telemetry_status": "not_executed",
                    "defect_count": 0,
                    "limitations": [],
                }
            )
    return ordered


def execute_suite(
    monorepo: Path,
    repositories: tuple[CatalogRepository, ...],
    *,
    telemetry_endpoint: str | None = None,
    telemetry_allow: bool = True,
    keep_clones: bool = False,
    limit: int | None = None,
    resume: bool = True,
) -> list[ExecutedRepositoryResult]:
    """Execute assessments for the curated catalog set (failure-isolated)."""

    import fcntl

    lock_path = (
        monorepo / ".codestrata-artifacts/validation/suites" / SUITE_ID / "suite.lock"
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_handle = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        lock_handle.close()
        raise RuntimeError("another sv17-13 suite runner holds suite.lock") from exc
    lock_handle.seek(0)
    lock_handle.truncate()
    lock_handle.write(f"pid={os.getpid()}\n")
    lock_handle.flush()

    try:
        return _execute_suite_locked(
            monorepo,
            repositories,
            telemetry_endpoint=telemetry_endpoint,
            telemetry_allow=telemetry_allow,
            keep_clones=keep_clones,
            limit=limit,
            resume=resume,
        )
    finally:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            lock_handle.close()


def _execute_suite_locked(
    monorepo: Path,
    repositories: tuple[CatalogRepository, ...],
    *,
    telemetry_endpoint: str | None = None,
    telemetry_allow: bool = True,
    keep_clones: bool = False,
    limit: int | None = None,
    resume: bool = True,
) -> list[ExecutedRepositoryResult]:
    clone_root = Path(tempfile.mkdtemp(prefix="cs-sv1713-root-"))
    venv_dir = Path(tempfile.mkdtemp(prefix="cs-sv1713-venv-"))
    engine_root = monorepo / "engine"
    print("sv17-13 installing codestrata CLI venv", flush=True)
    codestrata = _install_cli(engine_root, venv_dir)
    print("sv17-13 cli ready", flush=True)

    results: list[ExecutedRepositoryResult] = []
    targets = list(repositories if limit is None else repositories[:limit])
    progress_path = (
        monorepo / ".codestrata-artifacts/validation/suites" / SUITE_ID / "progress.jsonl"
    )
    progress_path.parent.mkdir(parents=True, exist_ok=True)

    already: dict[str, ExecutedRepositoryResult] = {}
    if resume and progress_path.is_file():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = str(row.get("repository_validation_id") or "")
            if not rid:
                continue
            already[rid] = ExecutedRepositoryResult(
                repository_validation_id=rid,
                language=row.get("language"),
                ecosystem=row.get("ecosystem"),
                tier=str(row.get("tier") or "tier3"),
                qualified_revision=str(row.get("qualified_revision") or ""),
                clone_status=str(row.get("clone_status") or "unknown"),
                assessment_status=str(row.get("assessment_status") or "unknown"),
                report_status=str(row.get("report_status") or "unknown"),
                head_status_summary=str(row.get("head_status_summary") or ""),
                eir_eligible=bool(row.get("eir_eligible")),
                telemetry_status=str(row.get("telemetry_status") or ""),
                defect_count=int(row.get("defect_count") or 0),
                limitations=list(row.get("limitations") or []),
                assessment_run_id=row.get("assessment_run_id"),
                assessment_artifact_ref=row.get("assessment_artifact_ref"),
                duration_seconds=row.get("duration_seconds"),
                exit_code=row.get("exit_code"),
                quality_class=row.get("quality_class"),
                detail=str(row.get("detail") or "resumed"),
            )

    try:
        for repo in targets:
            prior = already.get(repo.repository_id)
            if (
                resume
                and prior is not None
                and prior.assessment_status == "pass"
                and prior.assessment_run_id
            ):
                print(
                    f"sv17-13 resume-skip {repo.repository_id} "
                    f"run={prior.assessment_run_id}",
                    flush=True,
                )
                results.append(prior)
                continue
            print(
                f"sv17-13 assessing {repo.repository_id} tier={_tier_for(repo)}",
                flush=True,
            )
            one = execute_one_repository(
                monorepo,
                repo,
                codestrata=codestrata,
                venv_dir=venv_dir,
                clone_root=clone_root,
                telemetry_endpoint=telemetry_endpoint,
                telemetry_allow=telemetry_allow,
                keep_clone=keep_clones,
            )
            results.append(one)
            print(
                f"sv17-13 done {repo.repository_id} status={one.assessment_status} "
                f"run={one.assessment_run_id} duration={one.duration_seconds}",
                flush=True,
            )
            with progress_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(one), sort_keys=True) + "\n")
                handle.flush()
    finally:
        if not keep_clones:
            shutil.rmtree(clone_root, ignore_errors=True)
            shutil.rmtree(venv_dir, ignore_errors=True)
    return results
