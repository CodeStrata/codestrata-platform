"""CodeStrata branded CLI landing page (presentation only).

Shown for bare ``codestrata`` and ``codestrata welcome`` in interactive
terminals. Never changes assessment behavior, schemas, or AI. No telemetry.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from codestrata.cli.ux import (
    DOCS_HOME,
    WEBSITE,
    is_machine_mode,
    onboarding_completed,
)
from codestrata.package_metadata import get_package_version
from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION

# Design-system amber (governance/assets/DESIGN-SYSTEM.md).
# Foreground colors only — never bgcolor / reverse / screen fills.
AMBER = "#d98a3d"
AMBER_BRIGHT = "#eca860"
AMBER_DIM = "#b06a24"  # --amber-deep; panel borders
BRIGHT_WHITE = "bold bright_white"
WHITE = "white"
DIM = "dim"
CYAN = "cyan"

BRAND_STATEMENT = "CODE. UNDERSTOOD."
PRODUCT_CATEGORY = "Engineering Intelligence"
EDITION = "Community Edition"


class WordmarkSize(str, Enum):
    LARGE = "large"
    MEDIUM = "medium"
    COMPACT = "compact"


# Original CodeStrata wordmarks — layered "strata block" letterforms (not a
# third-party FIGlet font). Widths validated in tests for 40/60/80/100/120 cols.


# Large (~109 cols): premium double-line strata glyphs with letter spacing.
_WORDMARK_LARGE = """\
 ██████╗  ██████╗  ██████╗  ███████╗ ███████╗ ████████╗ ██████╗   █████╗  ████████╗  █████╗
██╔════╝ ██╔═══██╗ ██╔══██╗ ██╔════╝ ██╔════╝ ╚══██╔══╝ ██╔══██╗ ██╔══██╗ ╚══██╔══╝ ██╔══██╗
██║      ██║   ██║ ██║  ██║ █████╗   ███████╗    ██║    ██████╔╝ ███████║    ██║    ███████║
██║      ██║   ██║ ██║  ██║ ██╔══╝   ╚════██║    ██║    ██╔══██╗ ██╔══██║    ██║    ██╔══██║
╚██████╗ ╚██████╔╝ ██████╔╝ ███████╗ ███████║    ██║    ██║  ██║ ██║  ██║    ██║    ██║  ██║
 ╚═════╝  ╚═════╝  ╚═════╝  ╚══════╝ ╚══════╝    ╚═╝    ╚═╝  ╚═╝ ╚═╝  ╚═╝    ╚═╝    ╚═╝  ╚═╝"""

# Medium (~71 cols): readable block form for standard terminals.
_WORDMARK_MEDIUM = """\
█▀▀ █▀█ █▀▄ █▀▀ █▀▀ ▀█▀ █▀█ ▄▀█ ▀█▀ ▄▀█
█▄▄ █▄█ █▄▀ ██▄ ▄▄█  █  █▀▄ █▀█  █  █▀█"""

# Compact (~30 cols): dense box-drawing for narrow panes and 40-col terminals.
_WORDMARK_COMPACT = """\
╔═╗╔═╗╔╦╗╔═╗╔═╗╔╦╗╦═╗╔═╗╔╦╗╔═╗
║  ║ ║ ║║║╣ ╚═╗ ║ ╠╦╝╠═╣ ║ ╠═╣
╚═╝╚═╝═╩╝╚═╝╚═╝ ╩ ╩╚═╩ ╩ ╩ ╩ ╩"""


@dataclass(frozen=True, slots=True)
class StartHereContext:
    """Local-only cues for the Start Here panel (no repository scanning)."""

    has_config: bool
    has_report: bool
    config_path: Path
    reports_dir: Path


@dataclass(frozen=True, slots=True)
class StartHereContent:
    headline: str
    command: str


def terminal_columns(console: Console | None = None) -> int:
    """Best-effort terminal width for responsive layout."""

    if console is not None:
        return max(40, int(console.width or 80))
    try:
        size = shutil.get_terminal_size(fallback=(80, 24))
        return max(40, int(size.columns))
    except OSError:
        return 80


def select_wordmark_size(columns: int) -> WordmarkSize:
    if columns >= 120:
        return WordmarkSize.LARGE
    if columns >= 80:
        return WordmarkSize.MEDIUM
    return WordmarkSize.COMPACT


def wordmark_art(size: WordmarkSize | None = None, *, columns: int | None = None) -> str:
    """Return the ASCII CodeStrata wordmark for the given layout size."""

    resolved = size
    if resolved is None:
        resolved = select_wordmark_size(columns if columns is not None else terminal_columns())
    if resolved is WordmarkSize.LARGE:
        return _WORDMARK_LARGE
    if resolved is WordmarkSize.MEDIUM:
        return _WORDMARK_MEDIUM
    return _WORDMARK_COMPACT


def wordmark_width(art: str) -> int:
    lines = [line.rstrip("\n") for line in art.splitlines() if line.strip()]
    return max((len(line) for line in lines), default=0)


def is_shell_completion_context() -> bool:
    """Detect Click/Typer shell-completion invocations."""

    for key in os.environ:
        upper = key.upper()
        if upper.endswith("_COMPLETE") or upper.startswith("_TYPER_COMPLETE"):
            return True
    return False


def landing_suppressed(
    *,
    quiet: bool = False,
    json_output: bool = False,
) -> bool:
    """Return True when the branded landing must not render."""

    if quiet or json_output:
        return True
    if is_shell_completion_context():
        return True
    if os.environ.get("CODESTRATA_CLI_BANNER", "1").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return True
    if is_machine_mode(quiet=quiet, json_output=json_output):
        return True
    return False


def detect_start_here_context(
    *,
    cwd: Path | None = None,
    config_name: str = "codestrata.toml",
    reports_dirname: str = "reports",
) -> StartHereContext:
    """Inspect local files only — never scan repository contents."""

    root = cwd or Path.cwd()
    config_path = root / config_name
    reports_dir = root / reports_dirname
    has_report = False
    if reports_dir.is_dir():
        try:
            has_report = any(reports_dir.rglob("report.html"))
        except OSError:
            has_report = False
    return StartHereContext(
        has_config=config_path.is_file(),
        has_report=has_report,
        config_path=config_path,
        reports_dir=reports_dir,
    )


def start_here_content(
    context: StartHereContext,
    *,
    columns: int = 80,
) -> StartHereContent:
    if not context.has_config:
        return StartHereContent(
            headline="Initialize your workspace.",
            command="codestrata init",
        )
    if context.has_report:
        return StartHereContent(
            headline="Open your latest report.",
            command="codestrata open",
        )
    # Keep the assess command copyable without wrapping on narrow terminals.
    if columns < 80:
        assess_cmd = "codestrata assess --repo ."
        headline = "Generate your first assessment."
    else:
        assess_cmd = "codestrata assess --repo . --output reports --no-ai"
        headline = "Generate your first Engineering Assessment."
    return StartHereContent(
        headline=headline,
        command=assess_cmd,
    )


def _center_plain(text: str, width: int) -> str:
    """Legacy helper retained for tests / callers that center plain strings."""

    lines = text.splitlines()
    return "\n".join(line.center(width) if line.strip() else line for line in lines)


def _styled_console(*, force_mono: bool = False, width: int | None = None) -> Console:
    no_color = force_mono or not _color_allowed()
    # No Console-level style/theme: never paint a terminal-wide background.
    console = Console(
        force_terminal=True,
        no_color=no_color,
        highlight=False,
        soft_wrap=False,
        emoji=False,
        style=None,
    )
    if width is not None:
        console.size = (width, console.size.height or 24)
    return console


def _color_allowed() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    if os.environ.get("CODESTRATA_FORCE_COLOR", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True
    return bool(getattr(sys.stdout, "isatty", lambda: False)())


def _fg(text: str, style: str, *, enabled: bool) -> Text:
    """Foreground-only styled text (never bgcolor / reverse)."""

    return Text(text, style=style if enabled else "")


def _center_styled(content: str, style: str, width: int, *, enabled: bool) -> Text:
    """Center content without coloring padding spaces (avoids full-line washes)."""

    stripped = content.rstrip("\n")
    lines = stripped.splitlines() or [""]
    result = Text()
    for index, line in enumerate(lines):
        if index:
            result.append("\n")
        pad = max(0, (width - len(line)) // 2)
        if pad:
            result.append(" " * pad)
        result.append(line, style=style if enabled else "")
        trail = width - pad - len(line)
        if trail > 0:
            result.append(" " * trail)
    return result


def render_landing(
    *,
    console: Console | None = None,
    columns: int | None = None,
    cwd: Path | None = None,
    include_first_run: bool = True,
    force_mono: bool = False,
) -> None:
    """Render the branded CodeStrata landing page to the console."""

    active = console or _styled_console(force_mono=force_mono)
    width = columns if columns is not None else terminal_columns(active)
    # Rich only honors Console.width when height is also set (size property).
    height = getattr(active.size, "height", 24) or 24
    active.size = (width, height)
    size = select_wordmark_size(width)
    art = wordmark_art(size)

    # If the selected art is still wider than the terminal, step down.
    while wordmark_width(art) > width - 2 and size is not WordmarkSize.COMPACT:
        size = (
            WordmarkSize.MEDIUM
            if size is WordmarkSize.LARGE
            else WordmarkSize.COMPACT
        )
        art = wordmark_art(size)
    if wordmark_width(art) > width - 2:
        art = "C O D E S T R A T A"

    use_color = not active.no_color and _color_allowed() and not force_mono

    wordmark = _center_styled(art, AMBER, width, enabled=use_color)
    brand = _center_styled(BRAND_STATEMENT, BRIGHT_WHITE, width, enabled=use_color)
    category = _center_styled(PRODUCT_CATEGORY, WHITE, width, enabled=use_color)
    edition = _center_styled(EDITION, DIM, width, enabled=use_color)

    start = start_here_content(
        detect_start_here_context(cwd=cwd),
        columns=width,
    )
    start_body = Text(justify="center")
    start_body.append(start.headline)
    start_body.append("\n")
    start_body.append(
        start.command,
        style=CYAN if use_color else "bold",
    )
    # Panel: focal point — slightly wider horizontal padding; dim amber border.
    h_pad = 2 if width < 80 else 3
    needed = max(
        len(start.command) + (h_pad * 2) + 2,
        min(len(start.headline) + (h_pad * 2) + 2, width - 4),
        28 if width >= 60 else 24,
    )
    panel_w = max(24, min(needed, width - 2, 72 if width >= 80 else width - 2))
    start_panel = Panel(
        Align.center(start_body),
        title=_fg("Start Here", AMBER, enabled=use_color),
        border_style=AMBER_DIM if use_color else "dim",
        width=panel_w,
        padding=(1, h_pad),
        # Transparent content area — preserve the user's terminal background.
        style="",
    )

    # Next Steps: fixed-width right-aligned labels for a flush command column.
    label_width = 4 if width < 50 else 11  # "Open Report"
    steps = Table.grid(padding=(0, 2 if width >= 60 else 1), expand=False)
    steps.add_column(
        justify="right",
        width=label_width,
        style=AMBER if use_color else "bold",
        no_wrap=True,
    )
    steps.add_column(style=CYAN if use_color else "bold", no_wrap=True)
    if width < 50:
        steps.add_row("Init", "codestrata init")
        steps.add_row("Assess", "codestrata assess --repo .")
        steps.add_row("Open", "codestrata open")
    else:
        steps.add_row("Initialize", "codestrata init")
        steps.add_row("Assess", "codestrata assess --repo .")
        steps.add_row("Open Report", "codestrata open")

    version = get_package_version()
    meta = f"Engine {version} • {EDITION} • Schema {ASSESSMENT_JSON_SCHEMA_VERSION}"
    if len(meta) > width:
        meta = f"Engine {version} · Schema {ASSESSMENT_JSON_SCHEMA_VERSION}"
    docs_host = DOCS_HOME.replace("https://", "").replace("http://", "")
    site_host = WEBSITE.replace("https://", "").replace("http://", "")
    links = f"{docs_host} • {site_host} • codestrata --help"
    if len(links) > width:
        links = f"{docs_host} • codestrata --help"
    if len(links) > width:
        links = "codestrata --help"

    blocks: list[object] = []
    if include_first_run and not onboarding_completed():
        welcome = (
            "Welcome to CodeStrata Community Edition."
            if width >= 42
            else "Welcome to CodeStrata."
        )
        blocks.append(_center_styled(welcome, BRIGHT_WHITE, width, enabled=use_color))
        blocks.append(Text(""))

    # Compact vertical rhythm: wordmark → hierarchy → panel → steps → footer.
    blocks.extend(
        [
            wordmark,
            Text(""),
            brand,
            category,
            edition,
            Text(""),
            Align.center(start_panel, width=width),
            Text(""),
            _center_styled("Next Steps", AMBER, width, enabled=use_color),
            Align.center(steps, width=width),
            Text(""),
            _center_styled(meta, DIM, width, enabled=use_color),
            _center_styled(links, DIM, width, enabled=use_color),
        ]
    )

    active.print(Group(*blocks), soft_wrap=False)


def render_automation_fallback() -> None:
    """Concise bare-invocation output when the landing page is suppressed.

    Deterministic, non-Rich, no full command inventory. Exit code is owned by
    the caller (normally 0).
    """

    version = get_package_version()
    sys.stdout.write(
        f"CodeStrata Community Edition {version}\n"
        "Run `codestrata --help` for commands.\n"
    )


def show_bare_invocation(*, cwd: Path | None = None) -> None:
    """Single owner of bare ``codestrata`` output (landing or concise fallback).

    Never call ``ctx.get_help()`` here: with Rich markup mode, Click's
    ``get_help()`` prints the full help inventory to stdout as a side effect.
    """

    if landing_suppressed():
        render_automation_fallback()
        return
    render_landing(cwd=cwd)


# Back-compat alias used by older call sites / tests.
def show_landing_or_help(
    *,
    help_text: str = "",
    quiet: bool = False,
    json_output: bool = False,
    cwd: Path | None = None,
) -> None:
    """Deprecated wrapper — prefer ``show_bare_invocation``."""

    del help_text
    if landing_suppressed(quiet=quiet, json_output=json_output):
        render_automation_fallback()
        return
    render_landing(cwd=cwd)


__all__ = [
    "AMBER",
    "AMBER_BRIGHT",
    "BRAND_STATEMENT",
    "EDITION",
    "PRODUCT_CATEGORY",
    "StartHereContent",
    "StartHereContext",
    "WordmarkSize",
    "detect_start_here_context",
    "is_shell_completion_context",
    "landing_suppressed",
    "render_automation_fallback",
    "render_landing",
    "select_wordmark_size",
    "show_bare_invocation",
    "show_landing_or_help",
    "start_here_content",
    "terminal_columns",
    "wordmark_art",
    "wordmark_width",
]
