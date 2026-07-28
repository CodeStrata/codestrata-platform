"""Phase 14.2 release hardening tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS = ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from release.checksums import sha256_file, verify_sha256sums, write_sha256sums  # noqa: E402
from release.dependencies import build_dependency_inventory  # noqa: E402
from release.extraction import (  # noqa: E402
    assert_idempotent_export,
    tree_fingerprint,
    write_export_snapshot,
)
from release.inventory import build_surface_inventory  # noqa: E402
from release.secret_scan import scan_tree  # noqa: E402
from release.versions import check_version_consistency  # noqa: E402


def test_export_manifest_is_authoritative_v2() -> None:
    manifest = yaml.safe_load(
        (ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    assert manifest["version"] == 2
    assert manifest["manifest_id"] == "codestrata.community_release"
    assert "platform/" in manifest["release"]["forbidden_internal_paths"]
    defaults = manifest["defaults"]
    assert any("platform/" in item for item in defaults["forbid_path_substrings"])
    assert ".env" in "\n".join(defaults["exclude_globs"])


def test_surface_inventory_classifies_platform_commercial() -> None:
    inventory = build_surface_inventory(ROOT)
    assert inventory["surfaces"]["platform/"]["classification"] == "commercial_platform_only"
    names = {item["name"] for item in inventory["exports"]}
    assert "codestrata-engine" in names
    assert "codestrata-docs" in names


def test_secret_scan_redacts_and_blocks(tmp_path: Path) -> None:
    bad = tmp_path / "leak.txt"
    bad.write_text("token = 'AKIAIOSFODNN7EXAMPLE'\n", encoding="utf-8")
    findings = scan_tree(tmp_path)
    assert findings
    assert all("AKIAIOSFODNN7EXAMPLE" not in item.redacted_evidence for item in findings)
    assert any(item.release_blocking for item in findings)


def test_secret_scan_ignores_allowlisted_tests(tmp_path: Path) -> None:
    path = tmp_path / "tests" / "test_security.py"
    path.parent.mkdir(parents=True)
    path.write_text("AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
    findings = scan_tree(tmp_path)
    assert findings == []


def test_checksums_roundtrip(tmp_path: Path) -> None:
    one = tmp_path / "a.txt"
    one.write_text("hello\n", encoding="utf-8")
    sums = write_sha256sums([one], tmp_path / "SHA256SUMS")
    assert verify_sha256sums(sums, tmp_path) == []
    assert sha256_file(one) in sums.read_text(encoding="utf-8")


def test_dependency_inventory_has_engine() -> None:
    inventory = build_dependency_inventory(ROOT)
    names = {item["component"] for item in inventory["components"]}
    assert "codestrata-engine" in names


def test_version_consistency_engine_present() -> None:
    result = check_version_consistency(ROOT)
    assert result["versions"]["engine_pyproject"] == "0.1.0"
    assert result["passed"] is True


def test_extraction_idempotent_fingerprint(tmp_path: Path) -> None:
    repo = tmp_path / "codestrata-engine"
    repo.mkdir()
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    first = tree_fingerprint(repo)
    write_export_snapshot(
        staging_repo=repo,
        export_name="codestrata-engine",
        manifest_version=2,
        mode="first_time",
    )
    second = tree_fingerprint(repo)
    # Re-copy content without changing README
    (repo / "README.md").write_text("x\n", encoding="utf-8")
    third = tree_fingerprint(repo)
    assert assert_idempotent_export(first, third) == []
    assert (repo / ".codestrata-export-snapshot.json").is_file()
    payload = json.loads((repo / ".codestrata-export-snapshot.json").read_text())
    assert payload["mode"] == "first_time"
    assert second  # snapshot added a file
