"""Slice 14.12 — documentation deployment verification tests."""

from __future__ import annotations

import json
from pathlib import Path

from verification.documentation_deployment.checks import check_all
from verification.documentation_deployment.contract import (
    ASSETS_DIR,
    FORBIDDEN_EPIC_15_PATHS,
    POLICY_RELATIVE,
    WRANGLER_VERSION,
    monorepo_root_from_here,
)
from verification.documentation_deployment.output_alignment import compare_configured_vs_actual
from verification.documentation_deployment.runner import build_report, write_report

ROOT = monorepo_root_from_here()
DOCS = ROOT / "docs"


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_policy_contract() -> None:
    policy = _json(POLICY_RELATIVE)
    assert policy["policy_id"] == "codestrata-documentation-deployment-policy"
    assert policy["policy_version"] == "1.0"
    assert policy["package_root_model"] == "B_docs_package_root"
    assert policy["assets_directory"] == ASSETS_DIR
    assert policy["forbidden"]["start_epic_15"] is True


def test_package_root_model_b() -> None:
    assert not (ROOT / "package.json").is_file()
    assert (DOCS / "package.json").is_file()
    assert (DOCS / "wrangler.jsonc").is_file()


def test_output_alignment_rejects_wrong_monorepo_path() -> None:
    aligned, detail = compare_configured_vs_actual(DOCS, "docs/.vitepress/dist")
    assert aligned is False
    assert detail == "monorepo_relative_path"

    aligned_ok, detail_ok = compare_configured_vs_actual(DOCS, ASSETS_DIR)
    assert aligned_ok is True
    assert detail_ok == ".vitepress/dist"


def test_wrangler_local_dependency() -> None:
    pkg = json.loads((DOCS / "package.json").read_text(encoding="utf-8"))
    assert pkg["devDependencies"]["wrangler"] == WRANGLER_VERSION
    wrangler_pkg = DOCS / "node_modules" / "wrangler" / "package.json"
    assert wrangler_pkg.is_file()
    assert json.loads(wrangler_pkg.read_text(encoding="utf-8"))["version"] == WRANGLER_VERSION


def test_deploy_scripts_build_once() -> None:
    scripts = json.loads((DOCS / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert scripts["build"] == "vitepress build"
    assert "build" not in scripts["deploy:upload"].lower()
    assert "npm run build" not in scripts["deploy"]
    assert "npm run build" in scripts["deploy:local"]


def test_preflight_script_present() -> None:
    assert (DOCS / "scripts" / "deploy-check.mjs").is_file()


def test_slice_14_14_not_started() -> None:
    for relative in FORBIDDEN_EPIC_15_PATHS:
        assert not (ROOT / relative).exists(), relative


def test_runner_deterministic_and_passes() -> None:
    first = build_report(ROOT)
    second = build_report(ROOT)
    first_path = write_report(ROOT, first)
    second_path = write_report(ROOT, second)
    assert first_path.read_bytes() == second_path.read_bytes()
    payload = json.loads(first_path.read_text(encoding="utf-8"))
    assert payload["schema_name"] == "documentation-deployment-verification"
    assert payload["schema_version"] == "1.0.0"
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["failed_checks"] == 0
    assert payload["release_posture"]["start_epic_15"] is False
    assert payload["release_posture"]["no_production_deploy"] is True
    assert "/Users/" not in first_path.read_text(encoding="utf-8")


def test_static_checks_pass() -> None:
    checks, defects, _, _ = check_all(ROOT)
    assert not defects
    failed = [c for c in checks if not c.ok]
    assert not failed, failed[0].name if failed else ""
