"""Run a deterministic showcase assessment for a pinned real-world example."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from fetch_example import (  # noqa: E402
    FetchExampleError,
    fetch_example,
    list_manifest_ids,
    load_manifest,
    repo_root_from_here,
)


def _du_mb(path: Path) -> float:
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return round(total / (1024 * 1024), 2)


def _relpath(path: Path | None, root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "findings", "recommendations"):
            nested = value.get(key)
            if isinstance(nested, list):
                return nested
    return []


def _summarize_report(
    report: dict[str, Any],
    *,
    findings_payload: dict[str, Any] | None = None,
    recommendations_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assessment = report.get("assessment") if isinstance(report.get("assessment"), dict) else report
    findings = _as_list(assessment.get("findings"))
    if not findings and findings_payload:
        findings = _as_list(findings_payload.get("findings") or findings_payload)

    recommendations = _as_list(assessment.get("deterministic_recommendations"))
    if not recommendations:
        recommendations = _as_list(assessment.get("recommendations"))
    if not recommendations and recommendations_payload:
        recommendations = _as_list(
            recommendations_payload.get("recommendations") or recommendations_payload
        )

    technologies = assessment.get("technologies") or []
    tech_facts = ((assessment.get("repository_facts") or {}).get("technology") or {})
    detected = tech_facts.get("detected_technologies") if isinstance(tech_facts, dict) else None

    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for item in findings:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity") or "unknown")
        category = str(item.get("category") or item.get("finding_category") or "unknown")
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1

    exec_summary = assessment.get("executive_summary")
    if isinstance(exec_summary, dict) and exec_summary.get("findings_by_severity"):
        by_severity = {
            str(key): int(value) for key, value in exec_summary["findings_by_severity"].items()
        }

    def _top(
        items: list[Any],
        *,
        title_keys: tuple[str, ...],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            title = None
            for key in title_keys:
                if item.get(key):
                    title = str(item[key])
                    break
            rows.append(
                {
                    "title": title or item.get("id") or "item",
                    "severity": item.get("severity") or item.get("priority"),
                    "category": item.get("category") or item.get("finding_category"),
                    "id": item.get("id")
                    or item.get("finding_id")
                    or item.get("recommendation_id"),
                    "rule_id": item.get("rule_id"),
                }
            )
        return rows

    tech_names: list[str] = []
    if isinstance(detected, list) and detected:
        tech_names = [str(item) for item in detected]
    else:
        for tech in technologies if isinstance(technologies, list) else []:
            if isinstance(tech, dict):
                name = tech.get("name") or tech.get("technology") or tech.get("id")
                if name:
                    tech_names.append(str(name))
            elif tech:
                tech_names.append(str(tech))

    architecture: dict[str, Any] = {}
    facts = assessment.get("repository_facts") if isinstance(assessment, dict) else {}
    if isinstance(facts, dict) and isinstance(facts.get("architecture"), dict):
        architecture = dict(list(facts["architecture"].items())[:8])
    if isinstance(exec_summary, dict) and exec_summary.get("summary_text"):
        architecture = architecture or {"summary_text": exec_summary.get("summary_text")}

    roadmap = assessment.get("roadmap") or assessment.get("modernization_roadmap") or {}

    return {
        "technologies": tech_names[:40],
        "finding_count": len(findings),
        "recommendation_count": len(recommendations),
        "findings_by_severity": by_severity,
        "findings_by_category": by_category,
        "top_findings": _top(findings, title_keys=("title", "summary", "message", "rule_id")),
        "top_recommendations": _top(
            recommendations,
            title_keys=("title", "summary", "recommendation", "message", "description"),
        ),
        "architecture_summary": (
            architecture if isinstance(architecture, dict) else {"raw": architecture}
        ),
        "roadmap_summary": roadmap if isinstance(roadmap, dict) else {"raw": roadmap},
        "executive_summary_text": (
            exec_summary.get("summary_text") if isinstance(exec_summary, dict) else None
        ),
    }


def run_showcase(
    example_id: str,
    *,
    repo_root: Path,
    examples_root: Path,
    profile: str | None = None,
    force_fetch: bool = False,
    keep_fetch: bool = True,
) -> dict[str, Any]:
    manifest = load_manifest(example_id, examples_root=examples_root)
    fetch_info = fetch_example(
        example_id,
        repo_root=repo_root,
        examples_root=examples_root,
        force=force_fetch,
    )
    repo_path = Path(fetch_info["destination"])
    output_root = repo_root / "reports" / "showcases" / example_id
    output_root.mkdir(parents=True, exist_ok=True)

    selected_profile = profile or manifest.recommended_profile
    started = time.perf_counter()
    cmd = [
        "codestrata",
        "assess",
        "--repo",
        str(repo_path),
        "--output",
        str(output_root),
        "--profile",
        selected_profile,
        "--no-ai",
    ]
    completed = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    elapsed_s = round(time.perf_counter() - started, 2)

    report_html = next(iter(sorted(output_root.rglob("report.html"), reverse=True)), None)
    report_json_path = (
        report_html.with_name("report.json") if report_html is not None else None
    )
    findings_json_path = (
        report_html.with_name("findings.json") if report_html is not None else None
    )
    recommendations_json_path = (
        report_html.with_name("recommendations.json") if report_html is not None else None
    )
    report_payload = _read_json(report_json_path) if report_json_path else None
    findings_payload = _read_json(findings_json_path) if findings_json_path else None
    recommendations_payload = (
        _read_json(recommendations_json_path) if recommendations_json_path else None
    )
    summary_body = _summarize_report(
        report_payload or {},
        findings_payload=findings_payload,
        recommendations_payload=recommendations_payload,
    )

    try:
        version = subprocess.run(
            ["codestrata", "version"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip().splitlines()[0]
    except Exception:  # noqa: BLE001
        version = "unknown"

    public_summary = {
        "example_id": example_id,
        "project_name": manifest.name,
        "repository_url": manifest.normalized_url,
        "commit_sha": fetch_info["commit_sha"],
        "license_spdx": manifest.license_spdx,
        "attribution_url": manifest.attribution_url,
        "codestrata_version": version,
        "profile": selected_profile,
        "assess_command": [
            "codestrata",
            "assess",
            "--repo",
            f".codestrata-examples/{manifest.fetch_destination}",
            "--output",
            f"reports/showcases/{example_id}",
            "--profile",
            selected_profile,
            "--no-ai",
        ],
        "exit_code": completed.returncode,
        "elapsed_seconds": elapsed_s,
        "repository_size_mb": _du_mb(repo_path),
        "fetch": {
            "destination": f".codestrata-examples/{manifest.fetch_destination}",
            "reused": fetch_info.get("reused"),
            "provenance": (
                f".codestrata-examples/{manifest.fetch_destination}/"
                ".codestrata-example-provenance.json"
            ),
        },
        "report_paths": {
            "html": _relpath(report_html, repo_root),
            "json": _relpath(report_json_path, repo_root),
            "findings": _relpath(findings_json_path, repo_root),
            "recommendations": _relpath(recommendations_json_path, repo_root),
            "output_root": _relpath(output_root, repo_root),
        },
        "generated_at": datetime.now(UTC).isoformat(),
        **summary_body,
        "known_limitations": list(manifest.known_limitations),
    }

    summary_json = output_root / "showcase-summary.json"
    summary_json.write_text(
        json.dumps(public_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary_md = output_root / "showcase-summary.md"
    summary_md.write_text(_render_markdown(public_summary), encoding="utf-8")

    if not keep_fetch:
        shutil.rmtree(repo_path, ignore_errors=True)

    if completed.returncode != 0:
        detail = ((completed.stderr or "") + "\n" + (completed.stdout or ""))[-2000:]
        raise FetchExampleError(
            f"codestrata assess failed with exit {completed.returncode}. "
            f"See {summary_json}\n{detail}"
        )
    return public_summary


def _render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# Showcase: {summary.get('project_name')}",
        "",
        f"- Example ID: `{summary.get('example_id')}`",
        f"- Upstream: {summary.get('repository_url')}",
        f"- Pinned commit: `{summary.get('commit_sha')}`",
        f"- License: `{summary.get('license_spdx')}`",
        f"- CodeStrata version: `{summary.get('codestrata_version')}`",
        f"- Profile: `{summary.get('profile')}`",
        f"- Duration (s): {summary.get('elapsed_seconds')}",
        f"- Repository size (MB): {summary.get('repository_size_mb')}",
        f"- Findings: {summary.get('finding_count')}",
        f"- Recommendations: {summary.get('recommendation_count')}",
        "",
        "## Technologies",
        "",
    ]
    techs = summary.get("technologies") or []
    if techs:
        lines.extend(f"- {item}" for item in techs)
    else:
        lines.append("- (none recorded)")
    lines.extend(["", "## Top findings", ""])
    for item in summary.get("top_findings") or []:
        lines.append(f"- {item.get('title')} ({item.get('severity')}/{item.get('category')})")
    if not summary.get("top_findings"):
        lines.append("- (none)")
    lines.extend(["", "## Top recommendations", ""])
    for item in summary.get("top_recommendations") or []:
        lines.append(f"- {item.get('title')}")
    if not summary.get("top_recommendations"):
        lines.append("- (none)")
    lines.extend(["", "## Known limitations", ""])
    for item in summary.get("known_limitations") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_id", nargs="?", help="Showcase example id")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--force-fetch", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        examples_root = repo_root_from_here()
        repo_root = args.repo_root or (
            examples_root.parent if (examples_root / "real-world").is_dir() else examples_root
        )
        repo_root = repo_root.resolve()
        if args.list:
            print("\n".join(list_manifest_ids(examples_root=examples_root)))
            return 0
        if not args.example_id:
            parser.error("example_id required unless --list")
        summary = run_showcase(
            args.example_id,
            repo_root=repo_root,
            examples_root=examples_root,
            profile=args.profile,
            force_fetch=args.force_fetch,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except FetchExampleError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
