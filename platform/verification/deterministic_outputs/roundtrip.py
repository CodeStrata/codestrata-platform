"""Round-trip and hash-seed focused checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from codestrata.reporting.contract.canonical import strip_volatile_fields
from codestrata_platform.intelligence_reporting.domain.serialization import (
    from_stable_dict,
    report_to_stable_dict,
)

from verification.deterministic_outputs.fingerprints import (
    fingerprint_assessment_report,
    sha256_hex,
    stable_json_bytes,
)
from verification.deterministic_outputs.inputs import load_sample_report
from verification.deterministic_outputs.models import CheckResult, DeterminismWarning
from verification.engineering_intelligence.ingestion import build_pipeline_from_assessments
from verification.engineering_intelligence_quality.inputs import (
    load_prepared_assessments_from_sv10,
)


def check_roundtrip(monorepo: Path) -> tuple[list[CheckResult], list[DeterminismWarning]]:
    checks: list[CheckResult] = []
    warnings: list[DeterminismWarning] = []

    report = load_sample_report("cleanarchitecture", monorepo)
    fp1 = fingerprint_assessment_report(report)
    text = stable_json_bytes(strip_volatile_fields(report)).decode("utf-8")
    reloaded = json.loads(text)
    fp2 = fingerprint_assessment_report(reloaded)
    checks.append(
        CheckResult(
            name="roundtrip_assessment_fingerprint",
            ok=fp1 == fp2,
            detail=f"sha256={fp1[:16]}…",
            category="roundtrip",
        )
    )

    assessments, _sv11, _meta = load_prepared_assessments_from_sv10(monorepo=monorepo)
    pipeline = build_pipeline_from_assessments(
        assessments[:5],  # smaller subset for roundtrip speed; IDs still exercise ser/de
        title="SV.15 roundtrip subset",
    )
    payload = report_to_stable_dict(pipeline.report)
    again = report_to_stable_dict(from_stable_dict(payload))
    checks.append(
        CheckResult(
            name="roundtrip_eir_subset_report_id",
            ok=payload.get("report_id") == again.get("report_id"),
            detail=f"report_id={payload.get('report_id')}",
            category="roundtrip",
        )
    )

    # PYTHONHASHSEED subprocess probe (focused canonical JSON).
    script = (
        "import json,hashlib,os;"
        "d={'b':2,'a':1,'list':[3,1,2]};"
        "b=json.dumps(d,sort_keys=True,separators=(',',':')).encode();"
        "print(hashlib.sha256(b).hexdigest())"
    )
    digests: list[str] = []
    for seed in ("1", "2", "random"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        try:
            proc = subprocess.run(
                [sys.executable, "-c", script],
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            digests.append((proc.stdout or "").strip())
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                DeterminismWarning(
                    code="hash_seed_subprocess_failed",
                    detail=f"seed={seed} err={type(exc).__name__}",
                )
            )
            digests.append("")
    ok_hash = len(set(d for d in digests if d)) == 1 and all(digests)
    checks.append(
        CheckResult(
            name="roundtrip_python_hashseed_stable_json",
            ok=ok_hash,
            detail=f"digests={ [d[:12] for d in digests] }",
            category="roundtrip",
        )
    )
    return checks, warnings
