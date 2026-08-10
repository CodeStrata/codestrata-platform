"""Validation evidence manifest for public report URLs (Slice 17.23).

This is NOT production report-routing state. Production resolution remains in
the Community report publishing backend.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal
from urllib.request import Request, urlopen

SCHEMA = "public-report-urls-manifest:1.1"
PURPOSE = "Release Epic validation evidence — not production state"

ReportType = Literal["assessment", "engineering_intelligence"]
Status = Literal["published", "revoked", "retired"]

DEFAULT_RELATIVE = (
    ".codestrata-artifacts/validation/suites/release-v0.2.0/public-report-urls.json"
)


def default_manifest_path(monorepo: Path) -> Path:
    return monorepo / DEFAULT_RELATIVE


def _empty_manifest() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "purpose": PURPOSE,
        "assessments": [],
        "engineering_intelligence": [],
        "note": (
            "Append/update capable for Release Epic; do not treat as production inventory. "
            "Cloud lifecycle remains backend authority."
        ),
    }


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return _empty_manifest()
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise TypeError("manifest must be an object")
    return normalize_manifest(doc)


def normalize_manifest(doc: dict[str, Any]) -> dict[str, Any]:
    """Upgrade legacy 1.0 flat entries into 1.1 current/previous structure."""

    out = _empty_manifest()
    assessments: dict[str, dict[str, Any]] = {}
    eirs: dict[str, dict[str, Any]] = {}

    # New shape
    for item in doc.get("assessments") or []:
        if isinstance(item, dict) and item.get("repository_id"):
            assessments[str(item["repository_id"])] = dict(item)
    for item in doc.get("engineering_intelligence") or []:
        if isinstance(item, dict) and item.get("portfolio_id"):
            eirs[str(item["portfolio_id"])] = dict(item)

    # Legacy flat entries
    for item in doc.get("entries") or []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("report_kind") or item.get("report_type") or "assessment")
        url = str(item.get("public_url") or item.get("current_public_url") or "")
        status = str(item.get("status") or "published")
        if kind in {"assessment", "assessments"}:
            rid = str(item.get("repository_id") or "unknown")
            assessments[rid] = {
                "repository_id": rid,
                "report_type": "assessment",
                "current_public_url": url or None,
                "previous_public_url": None,
                "current_status": status if url else None,
                "previous_status": None,
                "last_verified_status": item.get("http_status_observed"),
                "source_slice": item.get("source_slice"),
                "note": item.get("note"),
            }
        elif kind in {"engineering_intelligence", "eir"}:
            pid = str(item.get("portfolio_id") or "unknown")
            eirs[pid] = {
                "portfolio_id": pid,
                "report_type": "engineering_intelligence",
                "current_public_url": url or None,
                "previous_public_url": None,
                "current_status": status if url else None,
                "previous_status": None,
                "last_verified_status": item.get("http_status_observed"),
                "source_slice": item.get("source_slice"),
                "note": item.get("note"),
            }

    # Legacy eir singleton
    legacy_eir = doc.get("eir")
    if isinstance(legacy_eir, dict) and legacy_eir.get("public_url"):
        pid = str(legacy_eir.get("portfolio_id") or "default")
        eirs.setdefault(
            pid,
            {
                "portfolio_id": pid,
                "report_type": "engineering_intelligence",
                "current_public_url": legacy_eir.get("public_url"),
                "previous_public_url": None,
                "current_status": legacy_eir.get("status") or "published",
                "previous_status": None,
                "last_verified_status": legacy_eir.get("http_status_observed"),
            },
        )

    out["assessments"] = sorted(assessments.values(), key=lambda e: str(e["repository_id"]))
    out["engineering_intelligence"] = sorted(
        eirs.values(), key=lambda e: str(e["portfolio_id"])
    )
    return out


def save_manifest(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_manifest(doc)
    path.write_text(
        json.dumps(normalized, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def upsert_published_url(
    path: Path,
    *,
    report_type: ReportType,
    logical_id: str,
    public_url: str,
    status: Status = "published",
    source_slice: str | None = None,
) -> dict[str, Any]:
    """Upsert current/previous rotation for one repository or portfolio."""

    doc = load_manifest(path)
    bucket_key = (
        "assessments" if report_type == "assessment" else "engineering_intelligence"
    )
    id_key = "repository_id" if report_type == "assessment" else "portfolio_id"
    entries = list(doc.get(bucket_key) or [])
    found: dict[str, Any] | None = None
    for item in entries:
        if str(item.get(id_key)) == logical_id:
            found = item
            break
    if found is None:
        found = {
            id_key: logical_id,
            "report_type": report_type,
            "current_public_url": None,
            "previous_public_url": None,
            "current_status": None,
            "previous_status": None,
            "last_verified_status": None,
        }
        entries.append(found)

    old_current = found.get("current_public_url")
    old_status = found.get("current_status")
    if old_current and old_current != public_url:
        # Rotate: previous becomes retired if a newer previous already exists.
        found["previous_public_url"] = old_current
        found["previous_status"] = old_status or "published"
    found["current_public_url"] = public_url
    found["current_status"] = status
    if source_slice:
        found["source_slice"] = source_slice
    doc[bucket_key] = entries
    save_manifest(path, doc)
    return found


def mark_revoked(path: Path, *, public_url: str) -> bool:
    doc = load_manifest(path)
    changed = False
    for bucket in ("assessments", "engineering_intelligence"):
        for item in doc.get(bucket) or []:
            if item.get("current_public_url") == public_url:
                item["current_status"] = "revoked"
                changed = True
            if item.get("previous_public_url") == public_url:
                item["previous_status"] = "revoked"
                changed = True
    if changed:
        save_manifest(path, doc)
    return changed


def verify_manifest_urls(path: Path, *, timeout: float = 8.0) -> dict[str, Any]:
    """GET-check current/previous/revoked URLs and update last_verified_status."""

    doc = load_manifest(path)
    results: list[dict[str, Any]] = []

    def _probe(url: str | None) -> int | None:
        if not url:
            return None
        try:
            req = Request(url, method="GET", headers={"User-Agent": "codestrata-sv17-23"})
            with urlopen(req, timeout=timeout) as resp:  # noqa: S310
                return int(resp.status)
        except Exception as exc:  # noqa: BLE001
            code = getattr(exc, "code", None)
            return int(code) if code else 0

    for bucket in ("assessments", "engineering_intelligence"):
        for item in doc.get(bucket) or []:
            cur = item.get("current_public_url")
            prev = item.get("previous_public_url")
            cur_status = item.get("current_status")
            prev_status = item.get("previous_status")
            cur_code = _probe(cur)
            prev_code = _probe(prev)
            ok_cur = True
            ok_prev = True
            if cur and cur_status == "published":
                ok_cur = cur_code == 200
            elif cur and cur_status in {"revoked", "retired"}:
                ok_cur = cur_code in {404, 410}
            if prev and prev_status == "published":
                ok_prev = prev_code == 200
            elif prev and prev_status in {"revoked", "retired"}:
                ok_prev = prev_code in {404, 410}
            item["last_verified_status"] = {
                "current_http": cur_code,
                "previous_http": prev_code,
                "current_ok": ok_cur,
                "previous_ok": ok_prev,
            }
            results.append(
                {
                    "id": item.get("repository_id") or item.get("portfolio_id"),
                    "current_ok": ok_cur,
                    "previous_ok": ok_prev,
                }
            )
    save_manifest(path, doc)
    return {"checked": len(results), "results": results}


__all__ = [
    "DEFAULT_RELATIVE",
    "SCHEMA",
    "default_manifest_path",
    "load_manifest",
    "mark_revoked",
    "normalize_manifest",
    "save_manifest",
    "upsert_published_url",
    "verify_manifest_urls",
]
