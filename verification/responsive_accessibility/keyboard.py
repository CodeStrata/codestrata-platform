"""Keyboard accessibility checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "keyboard"
_TRAP = re.compile(
    r"<(?:button|a|input|select|textarea|summary)[^>]*\btabindex\s*=\s*[\"']-1[\"']",
    re.IGNORECASE,
)


def check_keyboard(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, html in (("assessment", inv.assessment_html), ("eir", inv.eir_html)):
        add(f"keyboard:{surface}_skip_link", "skip-link" in html, "present")
        add(
            f"keyboard:{surface}_table_wrap_tabindex",
            'tabindex="0"' in html and "table-wrap" in html,
            "focusable_wrap",
        )
        traps = _TRAP.findall(html)
        add(
            f"keyboard:{surface}_no_focus_traps",
            not traps,
            "ok" if not traps else f"{len(traps)}",
        )

    add(
        "keyboard:eir_details_summary",
        "<details" in inv.eir_html.lower() and "<summary" in inv.eir_html.lower(),
        "native_disclosure",
    )
    add(
        "keyboard:assessment_focus_visible_rules",
        ":focus-visible" in inv.assessment_styles,
        "css_rules",
    )

    add(
        "keyboard:vscode_status_bar_a11y",
        "accessibilityInformation" in inv.vscode_status_bar,
        "declared",
    )
    vscode_blob = "\n".join(inv.vscode_sources.values())
    add(
        "keyboard:vscode_no_webview",
        "createWebviewPanel" not in vscode_blob and "WebviewView" not in vscode_blob,
        "native_only",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("keyboard", "keyboard navigation requirements not met"))
    return checks, defects
