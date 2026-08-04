"""Privacy / secret-safety scans for SV.8 artifacts."""

from __future__ import annotations

import re

from verification.website_export.contract import SAFETY_PATTERNS, UNSUPPORTED_SCORE_FRAGMENTS
from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_safety(verified: VerifiedExportInput) -> list[CheckResult]:
    blobs = {
        "json": verified.bundle.json_bytes.decode("utf-8"),
        "html": verified.bundle.html_bytes.decode("utf-8"),
        "manifest": verified.bundle.manifest_bytes.decode("utf-8"),
    }
    hits: list[str] = []
    for name, text in blobs.items():
        for label, pattern in SAFETY_PATTERNS:
            if re.search(pattern, text):
                hits.append(f"{name}:{label}")
        lowered = text.lower()
        for frag in UNSUPPORTED_SCORE_FRAGMENTS:
            if frag in lowered:
                hits.append(f"{name}:score:{frag}")
        # Affirmative industry-benchmark claims only (disclaimers allowed).
        if re.search(
            r"(?i)\bis an industry benchmark\b|\bare industry benchmarks\b",
            text,
        ):
            hits.append(f"{name}:industry_benchmark_claim")

    json_lower = blobs["json"].lower()
    structural_ok = (
        '"evidence_body"' not in json_lower
        and '"source_snippet"' not in json_lower
        and '"graph_payload"' not in json_lower
        and "canonical report json" not in json_lower
    )
    public_label_ok = "Public OSS report" in blobs["html"]
    private_leak = (
        "customer-private report" in blobs["html"].lower()
        and verified.policy.export_scope.value == "public_oss"
    )
    return [
        CheckResult(
            name="safety:no_secret_or_path_markers",
            ok=not hits,
            detail="ok" if not hits else ",".join(hits[:8]),
            category="safety",
        ),
        CheckResult(
            name="safety:no_evidence_graph_payload",
            ok=structural_ok,
            detail="projection structural",
            category="safety",
        ),
        CheckResult(
            name="safety:public_classification",
            ok=public_label_ok and not private_leak,
            detail=verified.bundle.document.classification,
            category="safety",
            scenario="A",
        ),
        CheckResult(
            name="safety:no_installation_style_ids_required",
            ok="installation_id" not in json_lower,
            detail="no installation_id",
            category="safety",
        ),
        CheckResult(
            name="safety:disclaimer_not_benchmark",
            ok="not" in blobs["html"].lower() and "industry benchmark" in blobs["html"].lower(),
            detail="honest disclaimer retained",
            category="safety",
        ),
    ]
