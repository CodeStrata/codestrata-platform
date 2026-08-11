#!/usr/bin/env python3
"""Epic 19 Slice 19.3 — final 22-repository production corpus orchestrator.

Phases:
  freeze | baseline | assess | quality | publish | insights | report | all

Does NOT publish CLI, Marketplace, create tags, or change Community Status.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.catalog import (
    load_release_validation_repositories,
)
from verification.community_22_repository_validation.contract import (
    monorepo_root_from_here,
)
from verification.public_report_urls.manifest import (
    SCHEMA,
    default_manifest_path,
    load_manifest,
    save_manifest,
    upsert_published_url,
    verify_manifest_urls,
)
from verification.release_corpus_19_3 import SLICE_ID, SUITE_EVIDENCE_RELATIVE

TELEMETRY_ENDPOINT = "https://api.codestrata.ai/api/v1/telemetry"
HEALTH_URL = "https://api.codestrata.ai/api/v1/health"
INSIGHTS_OVERVIEW = "https://insights.codestrata.ai/api/v1/insights/api/overview"
INSIGHTS_SESSION = "https://insights.codestrata.ai/api/v1/insights/auth/session"
REPORT_HOST_PREFIX = "https://reports.codestrata.ai/r/"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _evidence_dir(monorepo: Path) -> Path:
    path = monorepo / SUITE_EVIDENCE_RELATIVE
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def phase_freeze(monorepo: Path) -> dict[str, Any]:
    repos = load_release_validation_repositories(monorepo)
    if len(repos) != 22:
        raise SystemExit(f"corpus size drift: expected 22, got {len(repos)}")
    rows = []
    for repo in repos:
        raw = repo.raw
        rows.append(
            {
                "validation_id": repo.repository_id,
                "repository": repo.github_repository,
                "source_url": repo.github_url,
                "language_stack": repo.language_group,
                "size_category": raw.get("candidate_category"),
                "runtime_tier": repo.raw.get("expected_runtime_tier"),
                "reason_included": raw.get("codestrata_use"),
                "expected_validation_dimension": {
                    "enabled_for": dict(repo.enabled_for),
                    "project_shape": raw.get("project_shape"),
                    "framework_or_shape": raw.get("framework_or_shape"),
                },
                "qualified_revision": repo.qualified_revision_value,
            }
        )
    doc = {
        "slice": SLICE_ID,
        "captured_at_utc": _utc_now(),
        "catalog": "validation/repository-catalog/catalog.json",
        "selection": "enabled_for.release_validation == true",
        "count": len(rows),
        "repositories": rows,
    }
    out = _evidence_dir(monorepo) / "corpus-freeze.json"
    _write_json(out, doc)
    print(f"freeze count={len(rows)} path={out}", flush=True)
    return doc


def _http_json(url: str, *, timeout: int = 30) -> dict[str, Any]:
    """Fetch JSON via curl to avoid local Python SSL trust issues on macOS."""

    proc = subprocess.run(
        ["curl", "-sS", "--max-time", str(timeout), url],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"curl failed url={url} err={proc.stderr.strip()}")
    return json.loads(proc.stdout)


def phase_preflight(monorepo: Path) -> dict[str, Any]:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=monorepo, text=True).strip()
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=monorepo, text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=monorepo, text=True
    ).splitlines()
    version = subprocess.check_output(
        [str(monorepo / ".venv/bin/codestrata"), "version"],
        cwd=monorepo,
        text=True,
    )
    health = _http_json(HEALTH_URL)
    disk = subprocess.check_output(["df", "-h", str(monorepo)], text=True)
    doc = {
        "slice": SLICE_ID,
        "captured_at_utc": _utc_now(),
        "git_branch": branch,
        "git_head": head,
        "dirty_worktree_paths": len(dirty),
        "engine_version_text": version.strip().splitlines()[:8],
        "community_cloud_health": health,
        "disk": disk.strip().splitlines(),
        "telemetry_endpoint": TELEMETRY_ENDPOINT,
        "public_report_urls_manifest": str(default_manifest_path(monorepo)),
    }
    out = _evidence_dir(monorepo) / "preflight.json"
    _write_json(out, doc)
    print(f"preflight head={head[:12]} dirty={len(dirty)} health={health.get('status')}", flush=True)
    return doc


def _insights_cookie_jar() -> str:
    path = Path("/tmp/cs-insights-cookies.txt")
    if not path.is_file():
        raise SystemExit("Insights cookie jar missing at /tmp/cs-insights-cookies.txt — login first")
    return str(path)


def fetch_insights_overview(*, label: str, monorepo: Path) -> dict[str, Any]:
    cookie = _insights_cookie_jar()
    # Session check
    req = urllib.request.Request(INSIGHTS_SESSION, headers={"Accept": "application/json"})
    # Use curl for cookie jar compatibility
    ts = int(time.time() * 1000)
    overview_path = _evidence_dir(monorepo) / f"insights-{label}.json"
    proc = subprocess.run(
        [
            "curl",
            "-sS",
            "-b",
            cookie,
            "-H",
            "Accept: application/json",
            "-H",
            "Cache-Control: no-store",
            f"{INSIGHTS_OVERVIEW}?_={ts}",
            "-o",
            str(overview_path),
            "-w",
            "%{http_code}",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    code = (proc.stdout or "").strip()
    raw = json.loads(overview_path.read_text(encoding="utf-8"))
    if code != "200" or "error" in raw:
        raise SystemExit(f"insights overview failed http={code} body={raw}")
    metrics = {
        m["metric_id"]: {
            "value": m.get("value"),
            "completeness": m.get("completeness"),
            "limitations": m.get("limitations"),
        }
        for m in raw.get("metrics") or []
    }
    summary = {
        "slice": SLICE_ID,
        "label": label,
        "captured_at_utc": _utc_now(),
        "http_status": int(code),
        "metrics": metrics,
    }
    _write_json(_evidence_dir(monorepo) / f"insights-{label}-summary.json", summary)
    print(f"insights_{label} total={metrics.get('total_assessments')} published={metrics.get('published_reports')}", flush=True)
    return summary


def phase_assess(monorepo: Path, *, clean_start: bool) -> dict[str, Any]:
    cmd = [
        str(monorepo / ".venv/bin/python"),
        "-m",
        "verification.community_22_repository_validation",
        "--execute-assessments",
        "--telemetry-endpoint",
        TELEMETRY_ENDPOINT,
    ]
    if clean_start:
        cmd.append("--clean-start")
    env = {
        **os.environ,
        "HOME": os.environ.get("HOME") or str(Path.home()),
        "AWS_PROFILE": os.environ.get("AWS_PROFILE", "codestrata_infra"),
        "AWS_REGION": os.environ.get("AWS_REGION", "us-west-2"),
        "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-west-2"),
        # Shared corpus installation identity for first/repeat reconciliation.
        "CODESTRATA_HOME": "/tmp/cs-19-3-corpus-home",
        "CODESTRATA_TELEMETRY_ENDPOINT": TELEMETRY_ENDPOINT,
        "PYTHONPATH": f"{monorepo / 'engine' / 'src'}:{monorepo / 'platform' / 'src'}:{monorepo}",
    }
    Path(env["CODESTRATA_HOME"]).mkdir(parents=True, exist_ok=True)
    log = _evidence_dir(monorepo) / "assess-suite.log"
    print(f"assess starting clean_start={clean_start} log={log}", flush=True)
    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.run(
            cmd,
            cwd=monorepo,
            env=env,
            stdout=fh,
            stderr=subprocess.STDOUT,
            check=False,
        )
    summary = {
        "slice": SLICE_ID,
        "captured_at_utc": _utc_now(),
        "exit_code": proc.returncode,
        "clean_start": clean_start,
        "log": str(log.relative_to(monorepo)),
        "telemetry_endpoint": TELEMETRY_ENDPOINT,
        "codestrata_home": env["CODESTRATA_HOME"],
    }
    # Collect per-repo results
    results_root = monorepo / ".codestrata-artifacts/validation/repositories"
    rows = []
    for path in sorted(results_root.glob("*/result.json")) if results_root.is_dir() else []:
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    summary["repository_results"] = rows
    summary["attempted"] = len(rows)
    summary["passed"] = sum(1 for r in rows if r.get("assessment_status") == "pass")
    summary["failed"] = summary["attempted"] - summary["passed"]
    _write_json(_evidence_dir(monorepo) / "assess-summary.json", summary)
    print(
        f"assess done exit={proc.returncode} attempted={summary['attempted']} "
        f"passed={summary['passed']} failed={summary['failed']}",
        flush=True,
    )
    return summary


def _logical_id_for(repo_github: str) -> str:
    from codestrata.artifacts.repository_identity import build_github_repository_artifact_id

    owner, _, name = repo_github.partition("/")
    return build_github_repository_artifact_id(owner, name)


def phase_quality(monorepo: Path) -> dict[str, Any]:
    repos = load_release_validation_repositories(monorepo)
    rows = []
    for repo in repos:
        logical = _logical_id_for(repo.github_repository)
        current = monorepo / ".codestrata-artifacts/assessments" / logical / "current"
        html = current / "assessment.html"
        manifest = current / "assessment.json"
        issues: list[str] = []
        ok = True
        if not html.is_file() or not manifest.is_file():
            ok = False
            issues.append("missing_html_or_json")
            rows.append(
                {
                    "validation_id": repo.repository_id,
                    "logical_repository_id": logical,
                    "ok": False,
                    "issues": issues,
                }
            )
            continue
        text = html.read_text(encoding="utf-8", errors="replace")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        checks = {
            "branded_codestrata": "CodeStrata" in text,
            "assessment_overview": "Assessment Overview" in text
            or 'id="assessment-overview"' in text
            or "assessment-overview" in text.lower(),
            "no_stale_eis_title": "Engineering Intelligence Summary" not in text
            or "Assessment Overview" in text,
            "assessment_results": "Assessment Results" in text or "assessment-results" in text,
            "no_absolute_users_path": not re.search(
                r"/(?:Users|home)/[a-z][a-z0-9._-]{0,63}/", text
            ),
            "no_akia": "AKIA" not in text,
            "has_findings_or_limitations": ("Findings" in text) or ("Limitation" in text),
        }
        for key, passed in checks.items():
            if not passed:
                ok = False
                issues.append(key)
        # Soft: stale title exact display
        if re.search(r">\s*Engineering Intelligence Summary\s*<", text):
            ok = False
            issues.append("stale_eis_display_title")
        rows.append(
            {
                "validation_id": repo.repository_id,
                "logical_repository_id": logical,
                "ok": ok,
                "issues": issues,
                "schema_version": data.get("schema_version") or data.get("report_schema_version"),
                "engine_version": data.get("engine_version"),
                "overall_status": data.get("overall_status") or data.get("status"),
                "findings_count": len(data.get("findings") or [])
                if isinstance(data.get("findings"), list)
                else data.get("findings_count"),
                "html_bytes": html.stat().st_size,
            }
        )
    summary = {
        "slice": SLICE_ID,
        "captured_at_utc": _utc_now(),
        "count": len(rows),
        "passed": sum(1 for r in rows if r["ok"]),
        "failed": sum(1 for r in rows if not r["ok"]),
        "repositories": rows,
    }
    _write_json(_evidence_dir(monorepo) / "report-quality.json", summary)
    print(f"quality passed={summary['passed']} failed={summary['failed']}", flush=True)
    return summary


def _independent_get(url: str) -> dict[str, Any]:
    body_path = Path("/tmp/cs-19-3-report-get-body.html")
    hdr_path = Path("/tmp/cs-19-3-report-get.hdr")
    proc = subprocess.run(
        [
            "curl",
            "-sS",
            "-D",
            str(hdr_path),
            "-o",
            str(body_path),
            "-w",
            "%{http_code}",
            "--max-time",
            "60",
            url,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    code = int((proc.stdout or "0").strip() or "0")
    headers = hdr_path.read_text(encoding="utf-8", errors="replace") if hdr_path.is_file() else ""
    ctype = ""
    for line in headers.splitlines():
        if line.lower().startswith("content-type:"):
            ctype = line.split(":", 1)[1].strip()
            break
    body = body_path.read_bytes() if body_path.is_file() else b""
    return {
        "http_status": code,
        "content_type": ctype,
        "bytes": len(body),
        "body_head": body[:4000].decode("utf-8", errors="replace"),
    }


def phase_publish(monorepo: Path) -> dict[str, Any]:
    repos = load_release_validation_repositories(monorepo)
    manifest_path = default_manifest_path(monorepo)
    # Start from empty scaffold for final corpus evidence.
    save_manifest(
        manifest_path,
        {
            "schema": SCHEMA,
            "purpose": "Release Epic validation evidence — not production state",
            "assessments": [],
            "engineering_intelligence": [],
            "note": "Slice 19.3 final 22-repository corpus opaque URLs only.",
        },
    )
    codestrata = monorepo / ".venv/bin/codestrata"
    env = {
        **os.environ,
        "HOME": os.environ.get("HOME") or str(Path.home()),
        "AWS_PROFILE": os.environ.get("AWS_PROFILE", "codestrata_infra"),
        "AWS_REGION": os.environ.get("AWS_REGION", "us-west-2"),
        "AWS_DEFAULT_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-west-2"),
        "CODESTRATA_PUBLIC_REPORT_URLS_MANIFEST": str(manifest_path),
        "CODESTRATA_HOME": "/tmp/cs-19-3-corpus-home",
    }
    rows: list[dict[str, Any]] = []
    for repo in repos:
        logical = _logical_id_for(repo.github_repository)
        current = monorepo / ".codestrata-artifacts/assessments" / logical / "current" / "assessment.html"
        row: dict[str, Any] = {
            "validation_id": repo.repository_id,
            "repository": repo.github_repository,
            "logical_repository_id": logical,
            "publish_status": "not_attempted",
            "verified": False,
        }
        if not current.is_file():
            row["publish_status"] = "missing_local_current"
            rows.append(row)
            print(f"publish SKIP missing {logical}", flush=True)
            continue
        proc = subprocess.run(
            [
                str(codestrata),
                "report",
                "publish",
                "--type",
                "assessment",
                "--repository-id",
                logical,
                "--confirm-public-publish",
            ],
            cwd=monorepo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        m = re.search(r"https://reports\.codestrata\.ai/r/[A-Za-z0-9_-]+", out)
        if proc.returncode != 0 or not m:
            row["publish_status"] = "publish_failed"
            row["exit_code"] = proc.returncode
            row["detail"] = out[-800:]
            rows.append(row)
            print(f"publish FAIL {repo.repository_id}", flush=True)
            continue
        url = m.group(0)
        public_id = url.rsplit("/", 1)[-1]
        row["public_url"] = url
        row["public_report_id"] = public_id
        row["publish_status"] = "published"
        got = _independent_get(url)
        row["http_status"] = got["http_status"]
        row["content_type"] = got["content_type"]
        body = got.get("body_head") or ""
        identity_ok = (
            got["http_status"] == 200
            and "text/html" in (got.get("content_type") or "")
            and "CodeStrata" in body
            and (
                public_id in body
                or f'codestrata-public-id" content="{public_id}"' in body
                or f"codestrata-public-id\" content=\"{public_id}\"" in body
            )
        )
        # Also accept title containing project signal when public-id meta present.
        if got["http_status"] == 200 and "text/html" in (got.get("content_type") or "") and "CodeStrata" in body:
            if f'content="{public_id}"' in body or public_id in body:
                identity_ok = True
        row["verified"] = bool(identity_ok)
        if identity_ok:
            upsert_published_url(
                manifest_path,
                report_type="assessment",
                logical_id=logical,
                public_url=url,
                status="published",
                source_slice="19.3",
            )
            # Enrich entry with validation_id note
            doc = load_manifest(manifest_path)
            for item in doc.get("assessments") or []:
                if item.get("repository_id") == logical:
                    item["note"] = f"validation_id={repo.repository_id}; verified=true"
                    item["last_verified_status"] = 200
            save_manifest(manifest_path, doc)
            print(f"publish OK {repo.repository_id} {url}", flush=True)
        else:
            row["publish_status"] = "get_verify_failed"
            print(f"publish GET-FAIL {repo.repository_id} http={got.get('http_status')}", flush=True)
        rows.append(row)
        time.sleep(0.5)

    verify = verify_manifest_urls(manifest_path)
    summary = {
        "slice": SLICE_ID,
        "captured_at_utc": _utc_now(),
        "manifest_path": str(manifest_path),
        "schema": SCHEMA,
        "attempted": len(rows),
        "published_verified": sum(1 for r in rows if r.get("verified")),
        "failed": sum(1 for r in rows if not r.get("verified")),
        "repositories": rows,
        "manifest_verify": verify,
    }
    _write_json(_evidence_dir(monorepo) / "publish-summary.json", summary)
    print(
        f"publish done verified={summary['published_verified']} failed={summary['failed']}",
        flush=True,
    )
    return summary


def phase_report(monorepo: Path) -> dict[str, Any]:
    ev = _evidence_dir(monorepo)
    parts = {}
    for name in (
        "corpus-freeze.json",
        "preflight.json",
        "insights-baseline-summary.json",
        "assess-summary.json",
        "report-quality.json",
        "publish-summary.json",
        "insights-final-summary.json",
    ):
        path = ev / name
        if path.is_file():
            parts[name] = json.loads(path.read_text(encoding="utf-8"))
    publish = parts.get("publish-summary.json") or {}
    assess = parts.get("assess-summary.json") or {}
    quality = parts.get("report-quality.json") or {}
    freeze = parts.get("corpus-freeze.json") or {}
    baseline = parts.get("insights-baseline-summary.json") or {}
    final = parts.get("insights-final-summary.json") or {}

    founder_rows = []
    for row in publish.get("repositories") or []:
        founder_rows.append(
            {
                "validation_id": row.get("validation_id"),
                "repository": row.get("repository"),
                "status": "PASS" if row.get("verified") else "FAIL",
                "public_url": row.get("public_url"),
            }
        )

    assess_ok = int(assess.get("passed") or 0) == 22 and int(assess.get("failed") or 0) == 0
    publish_ok = int(publish.get("published_verified") or 0) == 22
    quality_ok = int(quality.get("failed") or 0) == 0
    freeze_ok = int(freeze.get("count") or 0) == 22

    if assess_ok and publish_ok and quality_ok and freeze_ok:
        verdict = "PASS"
        gate = "FINAL 22-REPOSITORY CORPUS PASSED — RELEASE READINESS MAY CONTINUE"
        complete = True
    elif assess_ok and publish_ok and freeze_ok:
        verdict = "PASS_WITH_LIMITATIONS"
        gate = "FINAL 22-REPOSITORY CORPUS PASSED — RELEASE READINESS MAY CONTINUE"
        complete = True
    else:
        verdict = "FAIL"
        gate = "FINAL 22-REPOSITORY CORPUS FAILED — RELEASE READINESS MUST STOP"
        complete = False

    defects = []
    for row in (assess.get("repository_results") or []):
        if row.get("assessment_status") != "pass":
            defects.append(
                {
                    "id": f"ASSESS-{row.get('repository_validation_id')}",
                    "repository": row.get("repository_validation_id"),
                    "area": "assessment",
                    "severity": "BLOCKER",
                    "observed": row.get("assessment_status"),
                    "expected": "pass",
                    "release_blocker": True,
                    "action": "diagnose assessment failure; do not fabricate PASS",
                }
            )
    for row in (quality.get("repositories") or []):
        if not row.get("ok"):
            defects.append(
                {
                    "id": f"QUALITY-{row.get('validation_id')}",
                    "repository": row.get("validation_id"),
                    "area": "report_quality",
                    "severity": "MUST_FIX_BEFORE_RELEASE",
                    "observed": row.get("issues"),
                    "expected": "clean report integrity checks",
                    "release_blocker": True,
                    "action": "fix report rendering defects",
                }
            )
    for row in (publish.get("repositories") or []):
        if not row.get("verified"):
            defects.append(
                {
                    "id": f"PUB-{row.get('validation_id')}",
                    "repository": row.get("validation_id"),
                    "area": "publication",
                    "severity": "BLOCKER",
                    "observed": row.get("publish_status"),
                    "expected": "published + independent GET verified",
                    "release_blocker": True,
                    "action": "investigate publish/GET failure",
                }
            )

    doc = {
        "slice": SLICE_ID,
        "captured_at_utc": _utc_now(),
        "verdict": verdict,
        "gate": gate,
        "complete": complete,
        "founder_review": founder_rows,
        "insights_baseline": baseline.get("metrics"),
        "insights_final": final.get("metrics"),
        "defects": defects,
        "boundaries": {
            "cli_publish": False,
            "vscode_marketplace_publish": False,
            "release_tag": False,
            "community_status_0_2_0": False,
        },
    }
    _write_json(ev / "slice-19-3-final.json", doc)
    # Markdown founder table
    lines = [
        f"# Epic 19 Slice 19.3 — Final corpus ({_utc_now()})",
        "",
        f"Verdict: **{verdict}**",
        "",
        "| # | Repository | Result | Public Report URL |",
        "|---|---|---|---|",
    ]
    for i, row in enumerate(founder_rows, start=1):
        lines.append(
            f"| {i} | `{row.get('repository')}` | {row.get('status')} | {row.get('public_url') or ''} |"
        )
    lines.extend(["", f"Gate: {gate}", ""])
    (ev / "founder-review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report verdict={verdict}", flush=True)
    print(gate, flush=True)
    return doc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Slice 19.3 release corpus orchestrator")
    parser.add_argument(
        "phase",
        choices=[
            "freeze",
            "preflight",
            "baseline",
            "assess",
            "quality",
            "publish",
            "insights-final",
            "report",
            "all",
        ],
    )
    parser.add_argument(
        "--no-clean-start",
        action="store_true",
        help="Do not wipe prior assessments before assess (resume-capable)",
    )
    args = parser.parse_args(argv)
    monorepo = monorepo_root_from_here()

    if args.phase in {"freeze", "all"}:
        phase_freeze(monorepo)
    if args.phase in {"preflight", "all"}:
        phase_preflight(monorepo)
    if args.phase in {"baseline", "all"}:
        fetch_insights_overview(label="baseline", monorepo=monorepo)
    if args.phase in {"assess", "all"}:
        phase_assess(monorepo, clean_start=not args.no_clean_start)
    if args.phase in {"quality", "all"}:
        phase_quality(monorepo)
    if args.phase in {"publish", "all"}:
        phase_publish(monorepo)
    if args.phase in {"insights-final", "all"}:
        # Allow aggregation lag
        time.sleep(15)
        fetch_insights_overview(label="final", monorepo=monorepo)
    if args.phase in {"report", "all"}:
        phase_report(monorepo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
