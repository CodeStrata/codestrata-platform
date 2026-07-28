"""Tests for the CodeStrata branded CLI landing experience."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from rich.console import Console
from typer.testing import CliRunner

from codestrata.cli import app
from codestrata.cli.landing import (
    BRAND_STATEMENT,
    EDITION,
    PRODUCT_CATEGORY,
    WordmarkSize,
    detect_start_here_context,
    landing_suppressed,
    render_landing,
    select_wordmark_size,
    show_landing_or_help,
    start_here_content,
    wordmark_art,
    wordmark_width,
)

runner = CliRunner()


def _render(columns: int, *, cwd: Path | None = None, first_run: bool = False) -> str:
    buf = StringIO()
    console = Console(
        file=buf,
        force_terminal=True,
        no_color=True,
        emoji=False,
        soft_wrap=False,
        legacy_windows=False,
    )
    console.size = (columns, 40)
    render_landing(
        console=console,
        columns=columns,
        cwd=cwd,
        include_first_run=first_run,
        force_mono=True,
    )
    return buf.getvalue()


def test_wordmark_sizes_and_widths() -> None:
    assert select_wordmark_size(120) is WordmarkSize.LARGE
    assert select_wordmark_size(100) is WordmarkSize.MEDIUM
    assert select_wordmark_size(80) is WordmarkSize.MEDIUM
    assert select_wordmark_size(79) is WordmarkSize.COMPACT
    assert select_wordmark_size(40) is WordmarkSize.COMPACT

    large = wordmark_art(WordmarkSize.LARGE)
    medium = wordmark_art(WordmarkSize.MEDIUM)
    compact = wordmark_art(WordmarkSize.COMPACT)
    assert wordmark_width(large) <= 118
    assert wordmark_width(medium) <= 78
    assert wordmark_width(compact) <= 38
    assert large != medium != compact
    assert len(large.splitlines()) >= 4
    assert len(compact.splitlines()) >= 2


def test_responsive_layouts_no_overflow(tmp_path: Path) -> None:
    for cols in (40, 60, 80, 100, 120):
        out = _render(cols, cwd=tmp_path)
        overs = [line for line in out.splitlines() if len(line) > cols]
        assert not overs, f"overflow at {cols}: {overs[:1]!r}"
        assert BRAND_STATEMENT in out
        assert PRODUCT_CATEGORY in out
        assert EDITION in out
        assert "Start Here" in out
        assert "Next Steps" in out
        assert "codestrata --help" in out
        assert "docs.codestrata.ai" in out
        assert "codestrata.ai" in out
        assert "Platform" not in out
        # Do not repeat the product name as a plain subtitle under the wordmark.
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        # Hierarchy order
        i_brand = out.index(BRAND_STATEMENT)
        i_cat = out.index(PRODUCT_CATEGORY)
        i_ed = out.index(EDITION)
        assert i_brand < i_cat < i_ed


def test_start_here_context_aware(tmp_path: Path) -> None:
    ctx = detect_start_here_context(cwd=tmp_path)
    assert ctx.has_config is False
    content = start_here_content(ctx, columns=100)
    assert "Initialize" in content.headline
    assert content.command == "codestrata init"

    (tmp_path / "codestrata.toml").write_text("[repository]\npath = \".\"\n", encoding="utf-8")
    ctx = detect_start_here_context(cwd=tmp_path)
    content = start_here_content(ctx, columns=100)
    assert "Engineering Assessment" in content.headline
    assert "codestrata assess" in content.command

    report = tmp_path / "reports" / "run" / "report.html"
    report.parent.mkdir(parents=True)
    report.write_text("<html></html>", encoding="utf-8")
    ctx = detect_start_here_context(cwd=tmp_path)
    content = start_here_content(ctx, columns=100)
    assert "Open" in content.headline
    assert content.command == "codestrata open"


def test_landing_suppression_rules(monkeypatch) -> None:
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("CODESTRATA_CLI_BANNER", raising=False)
    monkeypatch.delenv("CODESTRATA_CLI_MACHINE", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")

    assert landing_suppressed(quiet=True) is True
    assert landing_suppressed(json_output=True) is True

    monkeypatch.setenv("CI", "true")
    assert landing_suppressed() is True
    monkeypatch.delenv("CI", raising=False)

    monkeypatch.setenv("CODESTRATA_CLI_BANNER", "0")
    assert landing_suppressed() is True
    monkeypatch.delenv("CODESTRATA_CLI_BANNER", raising=False)

    monkeypatch.setenv("TERM", "dumb")
    assert landing_suppressed() is True
    monkeypatch.setenv("TERM", "xterm-256color")

    monkeypatch.setenv("_CODESTRATA_COMPLETE", "source_bash")
    assert landing_suppressed() is True
    monkeypatch.delenv("_CODESTRATA_COMPLETE", raising=False)


def test_show_landing_or_help_falls_back_when_suppressed(capsys) -> None:
    show_landing_or_help(help_text="HELP_OUTPUT", quiet=True)
    captured = capsys.readouterr()
    assert "HELP_OUTPUT" not in captured.out
    assert BRAND_STATEMENT not in captured.out
    assert "Run `codestrata --help` for commands." in captured.out
    assert "CodeStrata Community Edition" in captured.out


def test_show_landing_renders_when_allowed(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(
        "codestrata.cli.landing.landing_suppressed",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        "codestrata.cli.landing.onboarding_completed",
        lambda: True,
    )
    show_landing_or_help(help_text="HELP_OUTPUT", cwd=tmp_path)
    captured = capsys.readouterr()
    assert BRAND_STATEMENT in captured.out
    assert "HELP_OUTPUT" not in captured.out
    assert "Platform" not in captured.out


def test_codestrata_help_is_full_reference() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Primary workflow: assess" in result.stdout
    assert "Usage:" in result.stdout
    assert "assess" in result.stdout


def test_bare_codestrata_in_ci_shows_help_not_landing(monkeypatch) -> None:
    monkeypatch.setenv("CI", "true")
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage:" not in result.stdout
    assert "CODE. UNDERSTOOD." not in result.stdout
    assert "Run `codestrata --help` for commands." in result.stdout


def test_welcome_uses_landing_when_forced(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "codestrata.cli.welcome.landing_suppressed",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        "codestrata.cli.landing.onboarding_completed",
        lambda: True,
    )
    result = runner.invoke(app, ["welcome"])
    assert result.exit_code == 0
    assert BRAND_STATEMENT in result.stdout
    assert PRODUCT_CATEGORY in result.stdout
    assert EDITION in result.stdout


def test_no_color_monochrome_readable(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    out = _render(100, cwd=tmp_path)
    assert BRAND_STATEMENT in out
    assert "Start Here" in out
    # No ANSI escape sequences expected with force_mono render helper.
    assert "\x1b[" not in out
