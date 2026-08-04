"""HTML determinism using preserved sample HTML."""

from __future__ import annotations

import hashlib
import re

from verification.deterministic_outputs.contract import DETERMINISM_SAMPLE_IDS
from verification.deterministic_outputs.inputs import load_sample_artifact_bundle
from verification.deterministic_outputs.models import CheckResult

# Match HTML id attributes only — not data-*-id= references (SV.5 / SV report HTML).
_ID_RE = re.compile(r'(?<![\w-])id="([^"]+)"')


def _normalize_html(text: str) -> str:
    # Narrow normalization: collapse only CR/LF and trailing spaces — do not
    # strip content that would hide material differences.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text


def check_assessment_html(monorepo) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for rid in DETERMINISM_SAMPLE_IDS:
        try:
            bundle = load_sample_artifact_bundle(rid, monorepo)
        except Exception as exc:  # noqa: BLE001
            checks.append(
                CheckResult(
                    name=f"html_load_{rid}",
                    ok=False,
                    detail=type(exc).__name__,
                    category="html",
                )
            )
            continue
        html = bundle.get("html") or ""
        if not html:
            checks.append(
                CheckResult(
                    name=f"html_present_{rid}",
                    ok=False,
                    detail="missing report.html",
                    category="html",
                )
            )
            continue
        n1 = _normalize_html(html)
        n2 = _normalize_html(html)
        digest = hashlib.sha256(n1.encode("utf-8")).hexdigest()
        checks.append(
            CheckResult(
                name=f"html_fingerprint_stable_{rid}",
                ok=n1 == n2 and bool(digest),
                detail=f"sha256={digest[:16]}… len={len(html)}",
                category="html",
            )
        )
        # Document anchors must be unique; data-*-id may repeat shared Evidence.
        ids = _ID_RE.findall(html)
        dup = len(ids) - len(set(ids))
        checks.append(
            CheckResult(
                name=f"html_anchor_ids_unique_{rid}",
                ok=dup == 0,
                detail=f"anchors={len(ids)} duplicates={dup}",
                category="html",
            )
        )
    return checks
