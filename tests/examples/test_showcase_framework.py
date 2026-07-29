"""Offline unit tests for real-world showcase manifests and safe fetch helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = REPO_ROOT / "examples"
SCRIPTS = EXAMPLES_ROOT / "real-world" / "scripts"


def _load_module():
    """Import fetch_example without requiring package layout under examples/."""

    import importlib.util
    import sys

    path = SCRIPTS / "fetch_example.py"
    name = "fetch_example_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fetch_mod():
    return _load_module()


def _valid_manifest(**overrides):
    base = {
        "id": "demo-app",
        "name": "Demo App",
        "repository_url": "https://github.com/example/demo.git",
        "commit_sha": "a" * 40,
        "license_spdx": "MIT",
        "attribution_url": "https://github.com/example/demo",
        "primary_languages": ["Python"],
        "frameworks": ["Flask"],
        "expected_size_category": "small",
        "supported_capabilities": ["assess"],
        "recommended_profile": "community",
        "required_tools": ["git"],
        "fetch_destination": "demo-app",
        "runtime_category": "fast",
        "known_limitations": ["demo only"],
    }
    base.update(overrides)
    return base


def test_shipped_manifests_validate(fetch_mod):
    for example_id in fetch_mod.list_manifest_ids(examples_root=EXAMPLES_ROOT):
        manifest = fetch_mod.load_manifest(example_id, examples_root=EXAMPLES_ROOT)
        assert len(manifest.commit_sha) == 40
        assert manifest.license_spdx
        assert manifest.fetch_destination == Path(manifest.fetch_destination).name


def test_commit_sha_must_be_full_hex(fetch_mod):
    with pytest.raises(fetch_mod.FetchExampleError, match="40-character"):
        fetch_mod.validate_manifest_dict(_valid_manifest(commit_sha="main"))
    with pytest.raises(fetch_mod.FetchExampleError, match="40-character"):
        fetch_mod.validate_manifest_dict(_valid_manifest(commit_sha="abc123"))


def test_license_metadata_required(fetch_mod):
    data = _valid_manifest()
    data["license_spdx"] = ""
    with pytest.raises(fetch_mod.FetchExampleError, match="license"):
        fetch_mod.validate_manifest_dict(data)


def test_unknown_example_id(fetch_mod):
    with pytest.raises(fetch_mod.FetchExampleError, match="Unknown example id"):
        fetch_mod.load_manifest("does-not-exist", examples_root=EXAMPLES_ROOT)


def test_destination_path_safety(fetch_mod, tmp_path: Path):
    manifest = fetch_mod.validate_manifest_dict(_valid_manifest())
    with pytest.raises(fetch_mod.FetchExampleError, match="under"):
        fetch_mod.resolve_destination(
            manifest,
            repo_root=tmp_path,
            destination_override=tmp_path / "outside",
        )
    safe = fetch_mod.resolve_destination(manifest, repo_root=tmp_path)
    assert str(safe).startswith(str(fetch_mod.examples_fetch_root(tmp_path)))


def test_fetch_destination_rejects_traversal(fetch_mod):
    with pytest.raises(fetch_mod.FetchExampleError, match="fetch_destination"):
        fetch_mod.validate_manifest_dict(_valid_manifest(fetch_destination="../etc"))
    with pytest.raises(fetch_mod.FetchExampleError, match="fetch_destination"):
        fetch_mod.validate_manifest_dict(_valid_manifest(fetch_destination="a/b"))


def test_arbitrary_url_rejection(fetch_mod):
    with pytest.raises(fetch_mod.FetchExampleError, match="Arbitrary repository URLs"):
        fetch_mod.reject_arbitrary_url("https://github.com/evil/repo.git")


def test_submodules_not_approved(fetch_mod):
    with pytest.raises(fetch_mod.FetchExampleError, match="allow_submodules"):
        fetch_mod.validate_manifest_dict(_valid_manifest(allow_submodules=True))


def test_provenance_and_cleanup(fetch_mod, tmp_path: Path):
    manifests = tmp_path / "examples" / "real-world" / "manifests"
    manifests.mkdir(parents=True)
    sha = "b" * 40
    (manifests / "demo-app.yaml").write_text(
        yaml.safe_dump(_valid_manifest(commit_sha=sha)),
        encoding="utf-8",
    )
    examples_root = tmp_path / "examples"
    repo_root = tmp_path
    dest = fetch_mod.examples_fetch_root(repo_root) / "demo-app"
    dest.mkdir(parents=True)
    (dest / "README.md").write_text("demo\n", encoding="utf-8")
    manifest = fetch_mod.load_manifest("demo-app", examples_root=examples_root)
    provenance = fetch_mod.write_provenance(dest, manifest=manifest, resolved_sha=sha)
    payload = json.loads(provenance.read_text(encoding="utf-8"))
    assert payload["requested_commit_sha"] == sha
    assert payload["resolved_commit_sha"] == sha
    assert payload["license_spdx"] == "MIT"
    assert "not maintained by CodeStrata" in payload["codestrata_note"]
    cleaned = fetch_mod.cleanup_example(
        "demo-app", repo_root=repo_root, examples_root=examples_root
    )
    assert cleaned == dest
    assert not dest.exists()


def test_default_workspace_root_is_examples_repo(fetch_mod):
    """Standalone and monorepo: workspace is examples/, never its parent."""

    examples_root = fetch_mod.examples_root_from_here()
    assert examples_root == EXAMPLES_ROOT.resolve()
    workspace = fetch_mod.default_workspace_root(examples_root)
    assert workspace == EXAMPLES_ROOT.resolve()
    assert workspace != REPO_ROOT.resolve()
    assert (workspace / "real-world" / "manifests").is_dir()


def test_cli_default_repo_root_is_not_monorepo_parent(fetch_mod, monkeypatch):
    """``fetch_example.main`` without --repo-root must not use monorepo parent."""

    captured: dict[str, Path] = {}

    def fake_fetch(example_id, *, repo_root, examples_root, force=False):
        captured["repo_root"] = repo_root
        captured["examples_root"] = examples_root
        return {
            "example_id": example_id,
            "destination": str(repo_root / ".codestrata-examples" / "x"),
        }

    monkeypatch.setattr(fetch_mod, "fetch_example", fake_fetch)
    code = fetch_mod.main(["spring-petclinic"])
    assert code == 0
    assert captured["examples_root"] == EXAMPLES_ROOT.resolve()
    assert captured["repo_root"] == EXAMPLES_ROOT.resolve()
    assert captured["repo_root"] != REPO_ROOT.resolve()


def test_examples_ships_standalone_codestrata_toml():
    config = EXAMPLES_ROOT / "codestrata.toml"
    assert config.is_file()
    text = config.read_text(encoding="utf-8")
    assert 'profile = "community"' in text
    assert "[repository]" in text


def test_public_export_requires_examples_codestrata_toml():
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    examples_export = next(
        item for item in manifest["exports"] if item["name"] == "codestrata-examples"
    )
    required = examples_export["validation"]["require_files"]
    assert "codestrata.toml" in required


def test_gitignore_covers_fetched_examples():
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".codestrata-examples/" in gitignore


def test_public_export_excludes_fetched_trees():
    manifest = yaml.safe_load(
        (REPO_ROOT / "public-export-manifest.yaml").read_text(encoding="utf-8")
    )
    examples_export = next(
        item for item in manifest["exports"] if item["name"] == "codestrata-examples"
    )
    forbid = examples_export["validation"]["forbid_globs"]
    exclude = examples_export.get("exclude") or []
    assert any(".codestrata-examples" in pattern for pattern in forbid)
    assert any("showcases" in pattern for pattern in forbid + exclude)
    assert any("sample-" in pattern for pattern in forbid + exclude)
    required = examples_export["validation"]["require_files"]
    assert "real-world/THIRD_PARTY.md" in required
    assert "real-world/scripts/fetch_example.py" in required
    assert "codestrata.toml" in required
    assert not any(name.startswith("sample-") for name in required)
    assert "require_language_samples" not in examples_export["validation"]


def test_sample_apps_live_under_test_fixtures():
    fixtures = REPO_ROOT / "test-fixtures"
    for name in (
        "sample-js-app",
        "sample-python-app",
        "sample-java-app",
        "sample-php-app",
        "sample-csharp-app",
        "sample-reports",
    ):
        assert (fixtures / name).is_dir(), name
        assert not (REPO_ROOT / "examples" / name).exists(), name


def test_run_showcase_passes_local_codestrata_toml(monkeypatch, tmp_path: Path):
    """Showcase assess must use the examples-repo codestrata.toml when present."""

    import importlib.util
    import sys

    path = SCRIPTS / "run_showcase.py"
    name = "run_showcase_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = sys.modules.get(name)
    if module is None:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

    examples_root = tmp_path / "examples"
    manifests = examples_root / "real-world" / "manifests"
    manifests.mkdir(parents=True)
    sha = "c" * 40
    (manifests / "demo-app.yaml").write_text(
        yaml.safe_dump(_valid_manifest(commit_sha=sha, id="demo-app")),
        encoding="utf-8",
    )
    (examples_root / "codestrata.toml").write_text(
        '[repository]\npath = "."\nprofile = "community"\n',
        encoding="utf-8",
    )
    dest = examples_root / ".codestrata-examples" / "demo-app"
    dest.mkdir(parents=True)
    (dest / "README.md").write_text("ok\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_fetch(example_id, *, repo_root, examples_root, force=False):
        return {
            "example_id": example_id,
            "destination": str(dest),
            "commit_sha": sha,
        }

    def fake_run(cmd, cwd=None, capture_output=False, text=False, check=False):
        if cmd and cmd[0] == "codestrata" and "assess" in cmd:
            captured["cmd"] = list(cmd)
            captured["cwd"] = Path(cwd) if cwd else None

        class Result:
            returncode = 0
            stdout = "CodeStrata 0.1.0\n"
            stderr = ""

        return Result()

    monkeypatch.setattr(module, "fetch_example", fake_fetch)
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    summary = module.run_showcase(
        "demo-app",
        repo_root=examples_root,
        examples_root=examples_root,
    )
    assert summary["exit_code"] == 0
    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert "--config" in cmd
    assert str(examples_root / "codestrata.toml") in cmd
    assert captured["cwd"] == examples_root
