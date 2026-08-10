"""Hard and soft checks for Slice 17.26 public documentation reconciliation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from verification.community_public_documentation_reconciliation.contract import (
    CANONICAL_COMMUNITY_PRIVACY_URL,
    CONTRACT_RELATIVE,
    CS_FOOTER_RELATIVE,
    ENGINE_PRIVACY_RELATIVE,
    GITIGNORE_RELATIVE,
    LIVE_CORPORATE_HOME_URL,
    LIVE_DOCS_PRIVACY_URL,
    LIVE_REPORTS_FAVICON_URL,
    LIVE_REPORTS_LANDING_URL,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    PRIVACY_DOC_RELATIVE,
    PRIVACY_SECTION_MARKERS,
    REPORTS_APPLE_TOUCH,
    REPORTS_FAVICON_ICO,
    REPORTS_FAVICON_PNG,
    REPORTS_INDEX_RELATIVE,
    STALE_REPORT_PATH_LITERAL,
    STALE_REPORT_PATH_RE,
    WORKFLOW_REGISTER_RELATIVE,
)
from verification.community_public_documentation_reconciliation.helpers import (
    add_check,
    load_json,
    read_text,
)
from verification.community_public_documentation_reconciliation.models import (
    CheckResult,
    Defect,
)

_STALE_PATH_RE = re.compile(STALE_REPORT_PATH_RE)
_BARE_REPORTS_IGNORE_RE = re.compile(r"^/?reports/?\s*(?:#.*)?$")
_DOCS_REPORTS_IGNORE_RE = re.compile(r"^/?docs/reports(?:/.*)?\s*(?:#.*)?$")


def check_policy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}

    policy_path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", policy_path.is_file(), POLICY_RELATIVE, "policy")
    if policy_path.is_file():
        policy = load_json(policy_path)
        add_check(
            checks,
            defects,
            "policy:schema",
            policy.get("schema") == POLICY_SCHEMA,
            str(policy.get("schema")),
            "policy",
        )
        for key, expected in sorted(POLICY_REQUIRED_VALUES.items()):
            actual = policy.get(key)
            add_check(
                checks,
                defects,
                f"policy:{key}",
                actual == expected,
                f"{key}={actual}",
                "policy",
            )

    add_check(
        checks,
        defects,
        "contract:exists",
        (monorepo / CONTRACT_RELATIVE).is_file(),
        CONTRACT_RELATIVE,
        "policy",
    )

    # Boundary: this slice must keep 17.27 fenced off.
    add_check(
        checks,
        defects,
        "policy:start_slice_17_27_false",
        policy.get("start_slice_17_27") is False,
        f"start_slice_17_27={policy.get('start_slice_17_27')}",
        "policy",
    )

    wf_path = monorepo / WORKFLOW_REGISTER_RELATIVE
    if wf_path.is_file():
        wf = load_json(wf_path)
        add_check(
            checks,
            defects,
            "register:start_slice_17_26",
            wf.get("start_slice_17_26") is True,
            f"start_slice_17_26={wf.get('start_slice_17_26')}",
            "policy",
        )
        # Soft after 17.27 starts: historical 17.26 fence recorded start_slice_17_27=false;
        # workflow register may now show true without failing 17.26 re-runs.
        add_check(
            checks,
            defects,
            "register:start_slice_17_27_recorded",
            wf.get("start_slice_17_27") in (True, False),
            f"start_slice_17_27={wf.get('start_slice_17_27')}",
            "policy",
            soft=True,
        )

    return checks, defects, policy


def check_privacy_docs(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"exists": False, "markers_ok": False, "engine_link_ok": False}

    privacy_path = monorepo / PRIVACY_DOC_RELATIVE
    exists = privacy_path.is_file()
    summary["exists"] = exists
    add_check(checks, defects, "privacy:exists", exists, PRIVACY_DOC_RELATIVE, "privacy")

    missing: list[str] = []
    if exists:
        text = read_text(privacy_path)
        headings = [
            line.strip()
            for line in text.splitlines()
            if line.lstrip().startswith("#")
        ]
        heading_blob = "\n".join(headings)
        for marker in PRIVACY_SECTION_MARKERS:
            if marker not in heading_blob and marker not in text:
                missing.append(marker)
        markers_ok = not missing
        summary["markers_ok"] = markers_ok
        summary["missing_markers"] = missing
        add_check(
            checks,
            defects,
            "privacy:section_markers",
            markers_ok,
            "ok" if markers_ok else f"missing={missing}",
            "privacy",
        )

    engine_path = monorepo / ENGINE_PRIVACY_RELATIVE
    engine_text = read_text(engine_path)
    engine_ok = engine_path.is_file() and CANONICAL_COMMUNITY_PRIVACY_URL in engine_text
    summary["engine_link_ok"] = engine_ok
    add_check(
        checks,
        defects,
        "privacy:engine_link",
        engine_ok,
        ENGINE_PRIVACY_RELATIVE,
        "privacy",
    )

    footer_path = monorepo / CS_FOOTER_RELATIVE
    footer_text = read_text(footer_path)
    footer_ok = footer_path.is_file() and "cs-footer__tagline" in footer_text
    summary["footer_tagline_ok"] = footer_ok
    add_check(
        checks,
        defects,
        "docs:footer_tagline",
        footer_ok,
        CS_FOOTER_RELATIVE,
        "docs",
    )

    return checks, defects, summary


def _iter_docs_markdown(monorepo: Path) -> list[Path]:
    docs_root = monorepo / "docs"
    if not docs_root.is_dir():
        return []
    out: list[Path] = []
    for path in docs_root.rglob("*.md"):
        parts = set(path.parts)
        if "node_modules" in parts:
            continue
        # Exclude VitePress build output under docs/.vitepress/dist
        try:
            rel = path.relative_to(docs_root)
        except ValueError:
            continue
        if rel.parts[:2] == (".vitepress", "dist"):
            continue
        out.append(path)
    return sorted(out)


def check_stale_report_paths(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    hits: list[str] = []

    for path in _iter_docs_markdown(monorepo):
        text = read_text(path)
        rel = path.relative_to(monorepo).as_posix()
        if STALE_REPORT_PATH_LITERAL in text:
            hits.append(f"{rel}:literal")
        for match in _STALE_PATH_RE.finditer(text):
            hits.append(f"{rel}:{match.group(0)}")

    ok = not hits
    add_check(
        checks,
        defects,
        "docs:no_stale_report_paths",
        ok,
        "ok" if ok else f"hits={len(hits)}",
        "docs",
        classification="stale_report_path",
    )
    return checks, defects, {"stale_hits": hits[:20], "clean": ok}


def check_reports_landing(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    index_path = monorepo / REPORTS_INDEX_RELATIVE
    text = read_text(index_path)
    exists = index_path.is_file()
    summary["exists"] = exists
    add_check(checks, defects, "reports:index_exists", exists, REPORTS_INDEX_RELATIVE, "reports")

    privacy_ok = (
        exists
        and CANONICAL_COMMUNITY_PRIVACY_URL in text
        and 'href="https://codestrata.ai/privacy"' not in text
        and "href='https://codestrata.ai/privacy'" not in text
    )
    summary["privacy_link_ok"] = privacy_ok
    add_check(
        checks,
        defects,
        "reports:privacy_link",
        privacy_ok,
        CANONICAL_COMMUNITY_PRIVACY_URL if privacy_ok else "missing_or_corporate",
        "reports",
    )

    title_ok = exists and "Assessment Reports" in text
    h1_ok = exists and re.search(r"<h1[^>]*>\s*Assessment Reports\s*</h1>", text, re.I) is not None
    summary["title_ok"] = title_ok
    summary["h1_ok"] = h1_ok
    add_check(
        checks,
        defects,
        "reports:title_h1",
        title_ok and h1_ok,
        "Assessment Reports" if (title_ok and h1_ok) else "missing",
        "reports",
    )

    assets = {
        "favicon_ico": (monorepo / REPORTS_FAVICON_ICO).is_file(),
        "favicon_png": (monorepo / REPORTS_FAVICON_PNG).is_file(),
        "apple_touch": (monorepo / REPORTS_APPLE_TOUCH).is_file(),
    }
    summary["assets"] = assets
    assets_ok = all(assets.values())
    add_check(
        checks,
        defects,
        "reports:favicon_assets",
        assets_ok,
        str(assets),
        "reports",
    )

    favicon_linked = exists and (
        'href="/favicon.ico"' in text or 'href="favicon.ico"' in text
    )
    summary["favicon_linked"] = favicon_linked
    add_check(
        checks,
        defects,
        "reports:favicon_html_link",
        favicon_linked,
        "favicon.ico" if favicon_linked else "missing",
        "reports",
    )

    return checks, defects, summary


def check_gitignore(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"bare_reports_rule": False, "docs_reports_ignored": False}

    path = monorepo / GITIGNORE_RELATIVE
    text = read_text(path)
    add_check(checks, defects, "gitignore:exists", path.is_file(), GITIGNORE_RELATIVE, "gitignore")

    bare = False
    docs_ignored = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("!"):
            continue
        # Strip inline comments for pattern match of whole-line rules.
        pattern = line.split("#", 1)[0].strip()
        if _BARE_REPORTS_IGNORE_RE.match(pattern):
            bare = True
        if _DOCS_REPORTS_IGNORE_RE.match(pattern):
            docs_ignored = True

    summary["bare_reports_rule"] = bare
    summary["docs_reports_ignored"] = docs_ignored
    add_check(
        checks,
        defects,
        "gitignore:no_bare_reports",
        not bare,
        "clean" if not bare else "bare_reports_rule",
        "gitignore",
    )
    add_check(
        checks,
        defects,
        "gitignore:docs_reports_not_ignored",
        not docs_ignored,
        "clean" if not docs_ignored else "docs_reports_ignored",
        "gitignore",
    )
    return checks, defects, summary


def _http_get(url: str, *, accept: str = "*/*") -> tuple[int | None, str, str | None]:
    """Return (status, body_text, error_name)."""
    import ssl

    try:
        import certifi

        ctx = ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        ctx = ssl.create_default_context()

    try:
        req = Request(
            url,
            headers={"Accept": accept, "User-Agent": "codestrata-sv17-26"},
            method="GET",
        )
        with urlopen(req, timeout=15, context=ctx) as resp:  # noqa: S310 — public HTTPS probe
            status = int(getattr(resp, "status", 200) or 200)
            raw = resp.read()
            # Binary assets (favicon.ico) are not UTF-8 HTML.
            if "text/" in accept or accept == "*/*":
                try:
                    body = raw.decode("utf-8", errors="replace")
                except Exception:  # noqa: BLE001
                    body = ""
            else:
                body = ""
            return status, body, None
    except HTTPError as exc:
        status = int(exc.code)
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            body = ""
        return status, body, None
    except (URLError, TimeoutError, OSError) as exc:
        return None, "", type(exc).__name__


def check_live_soft(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    """Optional live HTTP probes — soft when network unavailable."""
    del monorepo  # local-only package root unused for live probes
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict[str, Any] = {}

    # Live docs privacy
    status, body, err = _http_get(LIVE_DOCS_PRIVACY_URL, accept="text/html")
    summary["docs_privacy"] = {"http_status": status, "error": err}
    docs_ok = status == 200
    add_check(
        checks,
        defects,
        "live:docs_privacy",
        docs_ok,
        f"http={status}" if status is not None else f"unreachable:{err}",
        "live",
        soft=True,
    )
    if not docs_ok:
        limitations.append("live_docs_privacy_unreachable")

    # Live reports favicon
    status, _body, err = _http_get(LIVE_REPORTS_FAVICON_URL)
    summary["reports_favicon"] = {"http_status": status, "error": err}
    fav_ok = status == 200
    add_check(
        checks,
        defects,
        "live:reports_favicon",
        fav_ok,
        f"http={status}" if status is not None else f"unreachable:{err}",
        "live",
        soft=True,
    )
    if not fav_ok:
        limitations.append("live_reports_favicon_unreachable")

    # Live reports landing privacy link
    status, body, err = _http_get(LIVE_REPORTS_LANDING_URL, accept="text/html")
    summary["reports_landing"] = {"http_status": status, "error": err}
    landing_privacy_ok = (
        status == 200
        and CANONICAL_COMMUNITY_PRIVACY_URL in body
        and "https://codestrata.ai/privacy" not in body
    )
    add_check(
        checks,
        defects,
        "live:reports_landing_privacy",
        landing_privacy_ok,
        (
            "ok"
            if landing_privacy_ok
            else (f"http={status}" if status is not None else f"unreachable:{err}")
        ),
        "live",
        soft=True,
    )
    if not landing_privacy_ok:
        limitations.append("live_reports_landing_privacy_mismatch")

    # Corporate site favicon — soft identification of stale relative / wrong asset
    status, body, err = _http_get(LIVE_CORPORATE_HOME_URL, accept="text/html")
    summary["corporate_home"] = {"http_status": status, "error": err}
    stale = False
    if status == 200:
        # Relative ../../favicon.svg or missing brand-local favicon.ico are stale signals.
        stale = (
            "../../favicon.svg" in body
            or 'href="../../favicon' in body
            or "href='../../favicon" in body
        )
        summary["corporate_home"]["favicon_stale"] = stale
    else:
        # Unreachable corporate home is also a soft limitation for favicon identity.
        stale = True
        summary["corporate_home"]["favicon_stale"] = True

    add_check(
        checks,
        defects,
        "live:corporate_favicon_identity",
        not stale,
        "current" if not stale else "stale_or_unreachable",
        "live",
        soft=True,
    )
    if stale:
        limitations.append("codestrata_ai_favicon_stale")

    return checks, defects, summary, limitations
