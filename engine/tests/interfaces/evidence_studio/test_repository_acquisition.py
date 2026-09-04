from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from codestrata.interfaces.evidence_studio.repository_acquisition import (
    GitHubRepositoryAcquirer,
    parse_public_github_url,
    validate_git_ref,
)

_REVISION = "a" * 40


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("https://github.com/pallets/markupsafe", "pallets/markupsafe"),
        ("https://github.com/pallets/markupsafe.git", "pallets/markupsafe"),
        ("https://github.com:443/pallets/markupsafe", "pallets/markupsafe"),
    ],
)
def test_public_github_url_is_canonicalized(value: str, expected: str) -> None:
    location = parse_public_github_url(value)
    assert location.display_name == expected
    assert location.canonical_url == f"https://github.com/{expected}.git"


@pytest.mark.parametrize(
    "value",
    [
        "http://github.com/owner/repo",
        "https://gitlab.com/owner/repo",
        "https://token@github.com/owner/repo",
        "https://github.com/owner/repo/issues",
        "https://github.com/owner/repo?token=secret",
        "https://github.com/owner/../repo",
        "git@github.com:owner/repo.git",
    ],
)
def test_non_public_or_ambiguous_github_urls_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        parse_public_github_url(value)


def test_git_ref_is_bounded_and_not_option_or_revision_syntax() -> None:
    assert validate_git_ref("release/v1.2.0") == "release/v1.2.0"
    assert validate_git_ref(" ") is None
    for value in ("--upload-pack=bad", "main..bad", "main@{1}", "refs//heads/main"):
        with pytest.raises(ValueError):
            validate_git_ref(value)


def test_acquirer_uses_safe_clone_and_content_addressed_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commands: list[tuple[list[str], dict[str, object]]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append((command, kwargs))
        if "clone" in command:
            checkout = Path(command[-1])
            checkout.mkdir(parents=True)
            (checkout / ".git").mkdir()
            (checkout / "README.md").write_text("fixture\n", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout=f"{_REVISION}\n", stderr="")

    monkeypatch.setattr(
        "codestrata.interfaces.evidence_studio.repository_acquisition.subprocess.run",
        fake_run,
    )
    acquirer = GitHubRepositoryAcquirer(cache_root=tmp_path / "cache")
    first = acquirer.acquire("https://github.com/pallets/markupsafe", "main")
    second = acquirer.acquire("https://github.com/pallets/markupsafe", "main")

    assert first.path == tmp_path / "cache" / "pallets" / "markupsafe" / _REVISION
    assert first.path.is_dir()
    assert first.cached is False
    assert second.cached is True
    clone_command, clone_options = next(
        item for item in commands if "clone" in item[0]
    )
    assert clone_command[-2] == "https://github.com/pallets/markupsafe.git"
    assert "--depth=1" in clone_command
    assert "--single-branch" in clone_command
    assert "--no-tags" in clone_command
    assert clone_command[clone_command.index("--branch") + 1] == "main"
    environment = clone_options["env"]
    assert isinstance(environment, dict)
    assert environment["GIT_TERMINAL_PROMPT"] == "0"
    assert environment["GIT_CONFIG_GLOBAL"] == os.devnull
