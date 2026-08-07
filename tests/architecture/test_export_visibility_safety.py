"""Export visibility, selective staging, and destination path safety."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
MANIFEST = REPO_ROOT / "public-export-manifest.yaml"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def export_mod():
    scripts_dir = str(SCRIPTS)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return _load_module(
        "export_public_repos_under_test",
        SCRIPTS / "export-public-repos.py",
    )


@pytest.fixture(scope="module")
def validate_mod():
    scripts_dir = str(SCRIPTS)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return _load_module(
        "validate_public_exports_under_test",
        SCRIPTS / "validate-public-exports.py",
    )


@pytest.fixture(scope="module")
def inventory():
    scripts_dir = str(SCRIPTS)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from release.inventory import (  # noqa: WPS433
        build_surface_inventory,
        destination_repository,
        export_classification,
        export_visibility,
        load_export_manifest,
    )

    return {
        "load": load_export_manifest,
        "visibility": export_visibility,
        "classification": export_classification,
        "destination": destination_repository,
        "build": build_surface_inventory,
    }


EXPECTED_MAPPING = {
    "codestrata-engine": {
        "source_root": "engine",
        "destination_repository": "codestrata-engine",
        "visibility": "public",
        "classification": "public_release",
    },
    "codestrata-examples": {
        "source_root": "examples",
        "destination_repository": "codestrata-examples",
        "visibility": "public",
        "classification": "public_release",
    },
    "codestrata-vscode": {
        "source_root": "vscode-plugin",
        "destination_repository": "codestrata-vscode",
        "visibility": "private",
        "classification": "private_release",
    },
    "codestrata-docs": {
        "source_root": "docs",
        "destination_repository": "codestrata-docs",
        "visibility": "private",
        "classification": "private_release",
    },
}


def test_five_repository_mappings_and_visibility(inventory) -> None:
    manifest = inventory["load"](REPO_ROOT)
    exports = {item["name"]: item for item in manifest["exports"]}
    assert set(exports) == set(EXPECTED_MAPPING)
    for name, expected in EXPECTED_MAPPING.items():
        item = exports[name]
        assert item["source_root"] == expected["source_root"]
        assert inventory["destination"](item) == expected["destination_repository"]
        assert inventory["visibility"](item) == expected["visibility"]
        assert inventory["classification"](item) == expected["classification"]
        assert "public_repository" not in item


def test_inventory_classifies_surfaces_and_exports(inventory) -> None:
    payload = inventory["build"](REPO_ROOT)
    assert payload["surfaces"]["engine/"]["classification"] == "public_release"
    assert payload["surfaces"]["examples/"]["classification"] == "public_release"
    assert payload["surfaces"]["docs/"]["classification"] == "private_release"
    assert "cursor-plugin/" not in payload["surfaces"]
    assert payload["surfaces"]["vscode-plugin/"]["classification"] == "private_release"
    assert "private_release" in payload["classifications_legend"]
    by_name = {item["name"]: item for item in payload["exports"]}
    assert by_name["codestrata-engine"]["classification"] == "public_release"
    assert by_name["codestrata-docs"]["classification"] == "private_release"
    assert by_name["codestrata-docs"]["visibility"] == "private"
    assert by_name["codestrata-docs"]["destination_repository"] == "codestrata-docs"


def test_destination_repository_legacy_alias(inventory) -> None:
    assert (
        inventory["destination"]({"name": "x", "public_repository": "legacy-name"}) == "legacy-name"
    )
    assert inventory["visibility"]({"name": "x"}) == "public"
    assert inventory["classification"]({"name": "x", "visibility": "private"}) == (
        "private_release"
    )


def test_selective_export_preserves_sibling_staging(tmp_path: Path, export_mod) -> None:
    staging = tmp_path / "staging"
    sibling = staging / "codestrata-docs"
    sibling.mkdir(parents=True)
    marker = sibling / "KEEP_ME.md"
    marker.write_text("sibling must survive selective export\n", encoding="utf-8")

    code = export_mod.main(
        [
            "--manifest",
            str(MANIFEST),
            "--staging",
            str(staging),
            "--repo",
            "codestrata-examples",
        ]
    )
    assert code == 0
    assert marker.is_file()
    assert (staging / "codestrata-examples" / "README.md").is_file()
    assert not (staging / "codestrata-engine").exists()


def test_selective_export_accepts_destination_repository_alias(tmp_path: Path, export_mod) -> None:
    staging = tmp_path / "staging"
    code = export_mod.main(
        [
            "--manifest",
            str(MANIFEST),
            "--staging",
            str(staging),
            "--repo",
            "codestrata-examples",
            "--repo",
            "codestrata-docs",
        ]
    )
    assert code == 0
    assert (staging / "codestrata-examples" / "README.md").is_file()
    assert (staging / "codestrata-docs" / "index.md").is_file()
    assert not (staging / "codestrata-engine").exists()


def test_full_clean_removes_entire_staging(tmp_path: Path, export_mod) -> None:
    staging = tmp_path / "staging"
    orphan = staging / "orphan-export"
    orphan.mkdir(parents=True)
    (orphan / "gone.txt").write_text("remove me\n", encoding="utf-8")

    code = export_mod.main(
        [
            "--manifest",
            str(MANIFEST),
            "--staging",
            str(staging),
            "--clean",
            "--repo",
            "codestrata-examples",
        ]
    )
    assert code == 0
    assert not orphan.exists()
    assert (staging / "codestrata-examples" / "README.md").is_file()


def test_destination_path_traversal_rejected(tmp_path: Path, export_mod) -> None:
    dest_root = tmp_path / "dest"
    dest_root.mkdir()
    with pytest.raises(ValueError, match="escapes staging root"):
        export_mod._safe_destination(dest_root, "../outside.txt")
    with pytest.raises(ValueError, match="escapes staging root"):
        export_mod._safe_destination(dest_root, "ok/../../outside.txt")

    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    examples = next(item for item in manifest["exports"] if item["name"] == "codestrata-examples")
    poisoned = dict(examples)
    poisoned["extra_includes"] = [
        {"from": "examples/README.md", "to": "../escaped.md"},
    ]
    with pytest.raises(ValueError, match="escapes staging root"):
        export_mod.export_one(
            root=REPO_ROOT,
            export=poisoned,
            staging_root=tmp_path / "staging",
            default_exclude=[],
            dry_run=False,
        )


def test_selective_validate_refresh_does_not_pass_clean_with_repo(
    validate_mod, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[list[str]] = []

    def fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
        captured.append(list(cmd))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(validate_mod.subprocess, "run", fake_run)
    # Skip real validation content by stopping after export refresh.
    monkeypatch.setattr(
        validate_mod,
        "validate_export",
        lambda **_kwargs: [],
    )
    code = validate_mod.main(
        [
            "--manifest",
            str(MANIFEST),
            "--repo",
            "codestrata-examples",
            "--skip-install",
        ]
    )
    assert code == 0
    assert captured, "expected export refresh invocation"
    assert "--clean" not in captured[0]
    assert "--repo" in captured[0]
    assert "codestrata-examples" in captured[0]


def test_full_validate_refresh_passes_clean(validate_mod, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
        captured.append(list(cmd))

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(validate_mod.subprocess, "run", fake_run)
    monkeypatch.setattr(validate_mod, "validate_export", lambda **_kwargs: [])
    code = validate_mod.main(
        [
            "--manifest",
            str(MANIFEST),
            "--skip-install",
            "--dry-run-export",
        ]
    )
    assert code == 0
    assert captured
    assert "--clean" in captured[0]
