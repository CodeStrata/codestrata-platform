"""Unit tests for Slice 13.14 clean-install verification."""

from __future__ import annotations

import json
from pathlib import Path

from verification.vscode_clean_install.contract import (
    SCHEMA_NAME,
    SCHEMA_VERSION,
    monorepo_root_from_here,
)
from verification.vscode_clean_install.runner import build_report, write_report


def test_build_report() -> None:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    assert report.schema_name == SCHEMA_NAME
    assert report.schema_version == SCHEMA_VERSION
    assert report.failed_checks == 0
    assert report.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert report.package_file_count > 0
    assert report.package_size_bytes > 0
    path = write_report(monorepo, report)
    text = Path(path).read_text(encoding="utf-8")
    assert "timestamp" not in text
    assert "/Users/" not in text
    assert "file://" not in text


def test_runner_deterministic() -> None:
    monorepo = monorepo_root_from_here()
    a = build_report(monorepo).to_dict()
    b = build_report(monorepo).to_dict()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_negative_forbidden_package_patterns() -> None:
    from verification.vscode_clean_install.checks import _forbidden_vsix_names

    hits = _forbidden_vsix_names(
        (
            "extension/out/extension.js",
            "extension/src/extension.ts",
            "extension/verification/report.json",
            "extension/out/test/foo.js",
        )
    )
    assert any("src/" in h for h in hits)
    assert any("verification" in h for h in hits)
    assert any("out/test" in h for h in hits)
