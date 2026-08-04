"""Empty / failure / identity scenarios for SV.8."""

from __future__ import annotations

import json
from pathlib import Path

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.website_export import (
    CONTENT_SECURITY_POLICY,
    ExportScope,
    RepositoryIdentityPolicy,
    WebsiteExportBuildPolicy,
    build_export_id,
    build_website_safe_export,
)
from codestrata_platform.intelligence_reporting.application.website_export.manifest import (
    sha256_bytes,
)
from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
    default_demo_directory,
)
from codestrata_platform.intelligence_reporting.domain._safety import reject_unsafe_text
from codestrata_platform.intelligence_reporting.infrastructure.static_export_writer import (
    StaticIntelligenceExportWriter,
)

from verification.website_export.inputs import VerifiedExportInput
from verification.website_export.models import CheckResult


def check_anonymized_scope(verified: VerifiedExportInput) -> list[CheckResult]:
    policy = WebsiteExportBuildPolicy(
        export_scope=ExportScope.ANONYMIZED_EXTERNAL,
        repository_identity_policy=RepositoryIdentityPolicy.ANONYMIZE_ALWAYS,
    )
    # Rebuild quality token into a fresh export by exporting with anonymized policy
    # against the public report — product may reject scope mismatch. Catch either
    # successful anonymized projection or fail-closed mismatch.
    try:
        bundle = build_website_safe_export(verified.report, policy=policy)
        aliases = [alias for alias, _ in bundle.document.repository_population]
        ok = (
            all(a.startswith("repository-") for a in aliases)
            and len(set(aliases)) == len(aliases)
            and "Public OSS report" not in bundle.document.classification
        )
        detail = f"aliases={len(aliases)} class={bundle.document.classification}"
        closed = False
    except InvalidValueError as exc:
        ok = True
        closed = True
        detail = f"fail_closed:{getattr(exc, 'reason_code', 'invalid')}"
    return [
        CheckResult(
            name="scenario:anonymized_external",
            ok=ok,
            detail=detail,
            category="scenarios",
            scenario="J",
        ),
        CheckResult(
            name="scenario:anonymized_or_fail_closed",
            ok=ok or closed,
            detail=detail,
            category="scenarios",
            scenario="J",
        ),
    ]


def check_identity_alias_stability(verified: VerifiedExportInput) -> list[CheckResult]:
    # Public OSS uses display names when permitted; aliases must be stable across runs.
    left = build_website_safe_export(verified.report, policy=verified.policy)
    right = build_website_safe_export(verified.report, policy=verified.policy)
    return [
        CheckResult(
            name="scenario:population_stable",
            ok=left.document.repository_population == right.document.repository_population,
            detail=f"count={len(left.document.repository_population)}",
            category="scenarios",
            scenario="A",
        ),
        CheckResult(
            name="scenario:drilldowns_unique",
            ok=len({d.drilldown_id for d in left.document.repository_drilldowns})
            == len(left.document.repository_drilldowns)
            == 5,
            detail="unique drilldowns",
            category="scenarios",
            scenario="A",
        ),
    ]


def check_unsafe_text_rejection() -> list[CheckResult]:
    checks: list[CheckResult] = []
    for scenario, value in (
        ("N", "/Users/example/project/src/main.py"),
        ("O", "AKIAIOSFODNN7EXAMPLE"),
    ):
        rejected = False
        try:
            reject_unsafe_text(value, label="sv8_probe")
        except Exception:  # noqa: BLE001
            rejected = True
        checks.append(
            CheckResult(
                name=f"scenario:unsafe_reject:{scenario}",
                ok=rejected,
                detail="reject_unsafe_text",
                category="scenarios",
                scenario=scenario,
            )
        )
    # HTML/export validation rejects script/file markers (domain reject_unsafe_text
    # focuses on paths/secrets; Epic 6.10 HTML validator covers markup injection).
    from codestrata_platform.intelligence_reporting.application.website_export.validation import (
        validate_html_artifact,
    )

    for scenario, html in (
        ("L", "<!doctype html><html><body><script>x</script></body></html>"),
        ("M", "<!doctype html><html><body><a href='file:///tmp/x'>x</a></body></html>"),
    ):
        rejected = False
        try:
            validate_html_artifact(html)
        except Exception:  # noqa: BLE001
            rejected = True
        checks.append(
            CheckResult(
                name=f"scenario:html_unsafe_reject:{scenario}",
                ok=rejected,
                detail="validate_html_artifact",
                category="scenarios",
                scenario=scenario,
            )
        )
    return checks


def check_policy_token_required(verified: VerifiedExportInput) -> list[CheckResult]:
    meta = verified.bundle.document.export_metadata
    assert meta is not None
    mutated = build_export_id(
        source_report_id=meta.export_id,
        interpretation_policy_bundle_id=meta.interpretation_policy_bundle_id,
        export_policy_token="",
        export_schema_version="1.0",
        artifact_template_version="eir-export-artifacts-v1",
    )
    return [
        CheckResult(
            name="scenario:empty_policy_token_changes_identity",
            ok=mutated != meta.export_id,
            detail="token participates",
            category="scenarios",
            scenario="T",
        ),
        CheckResult(
            name="scenario:csp_constant_present",
            ok="script-src 'none'" in CONTENT_SECURITY_POLICY,
            detail="csp",
            category="scenarios",
        ),
    ]


def check_oss_demonstration_regression() -> list[CheckResult]:
    demo = default_demo_directory()
    json_path = demo / "engineering-intelligence-report.json"
    html_path = demo / "engineering-intelligence-report.html"
    manifest_path = demo / "export-manifest.json"
    checks = [
        CheckResult(
            name="demo:files_exist",
            ok=json_path.is_file() and html_path.is_file() and manifest_path.is_file(),
            detail="platform/demo artifacts",
            category="demo",
        )
    ]
    if not all(p.is_file() for p in (json_path, html_path, manifest_path)):
        return checks

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = {item["filename"]: item for item in manifest.get("artifacts", [])}
    json_bytes = json_path.read_bytes()
    html_bytes = html_path.read_bytes()
    checks.extend(
        [
            CheckResult(
                name="demo:manifest_json_digest",
                ok=artifacts["engineering-intelligence-report.json"]["sha256"]
                == sha256_bytes(json_bytes),
                detail="digest match",
                category="demo",
            ),
            CheckResult(
                name="demo:manifest_html_digest",
                ok=artifacts["engineering-intelligence-report.html"]["sha256"]
                == sha256_bytes(html_bytes),
                detail="digest match",
                category="demo",
            ),
            CheckResult(
                name="demo:schema_1_0",
                ok=manifest.get("export_schema_version") == "1.0",
                detail=str(manifest.get("export_schema_version")),
                category="demo",
            ),
            CheckResult(
                name="demo:public_classification",
                ok=manifest.get("classification") == "Public OSS report",
                detail=str(manifest.get("classification")),
                category="demo",
            ),
            CheckResult(
                name="demo:five_repositories",
                ok=int(manifest.get("repository_count", 0)) == 5,
                detail=str(manifest.get("repository_count")),
                category="demo",
            ),
            CheckResult(
                name="demo:no_path_leak",
                ok="/Users/" not in json_bytes.decode("utf-8", errors="ignore")
                and "file://" not in html_bytes.decode("utf-8", errors="ignore").lower(),
                detail="path-free",
                category="demo",
            ),
            CheckResult(
                name="demo:distinct_from_sv6_report_id",
                ok=str(manifest.get("source_report_id", "")).startswith("eir:")
                and str(manifest.get("source_report_id"))
                != "eir:394b8574e3bc83b0878dc031",
                detail="demo uses its own curated EIR",
                category="demo",
            ),
        ]
    )
    return checks


def check_writer_partial_failure_contract(tmp_path: Path, verified: VerifiedExportInput) -> list[CheckResult]:
    """Overwrite refusal must leave the prior complete artifact set intact."""

    writer = StaticIntelligenceExportWriter()
    out = tmp_path / "partial"
    writer.write(verified.bundle, out)
    before = {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}
    blocked = False
    try:
        writer.write(verified.bundle, out, overwrite=False)
    except InvalidValueError:
        blocked = True
    after = {p.name: p.read_bytes() for p in out.iterdir() if p.is_file()}
    return [
        CheckResult(
            name="scenario:partial_overwrite_blocked",
            ok=blocked and before == after,
            detail="artifacts unchanged",
            category="scenarios",
            scenario="R",
        )
    ]
