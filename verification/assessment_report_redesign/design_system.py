"""Design-system token consumption checks."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.assessment_report_redesign.contract import (
    DESIGN_SYSTEM_CATALOG,
    DESIGN_SYSTEM_TOKENS,
    ENGINE_STYLES,
    ENGINE_TOKENS,
    LEGACY_AMBER_HEX,
)
from verification.assessment_report_redesign.models import CheckResult, Defect


def check_design_system(monorepo: Path) -> tuple[list[CheckResult], list[Defect], bool]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    catalog = json.loads((monorepo / DESIGN_SYSTEM_CATALOG).read_text(encoding="utf-8"))
    colors = catalog.get("colors", {})
    engine_tokens = (monorepo / ENGINE_TOKENS).read_text(encoding="utf-8")
    engine_styles = (monorepo / ENGINE_STYLES).read_text(encoding="utf-8")
    ds_tokens = (monorepo / DESIGN_SYSTEM_TOKENS).read_text(encoding="utf-8")

    consumed = (
        "codestrata.design_system.tokens" in engine_styles
        and "DESIGN_TOKENS_CSS" in engine_styles
        and "codestrata-visual-design-system:1.0" in engine_tokens
    )
    checks.append(
        CheckResult(
            "design_system:styles_import_tokens",
            consumed,
            "embedded",
            "design_system",
        )
    )
    for key, expected in (
        ("canvas", "#f4f6f3"),
        ("ink", "#111815"),
        ("teal", "#16756a"),
        ("teal_dark", "#0f5d54"),
        ("rust", "#a04b17"),
        ("blue", "#4d6885"),
    ):
        ok = colors.get(key) == expected and expected in engine_tokens
        checks.append(
            CheckResult(
                f"design_system:brand_{key}",
                ok,
                expected,
                "design_system",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    "design-system integration defect",
                    key,
                    expected,
                    str(colors.get(key)),
                )
            )

    checks.append(
        CheckResult(
            "design_system:ds_tokens_authority",
            "--cs-teal-dark: #0f5d54" in ds_tokens,
            "teal_dark",
            "design_system",
        )
    )
    checks.append(
        CheckResult(
            "design_system:wrap_1160",
            "1160px" in engine_tokens,
            "1160",
            "design_system",
        )
    )
    checks.append(
        CheckResult(
            "design_system:radius_6",
            "--cs-radius: 6px" in engine_tokens,
            "6px",
            "design_system",
        )
    )

    # Brand hex should not be freely scattered in component CSS outside tokens.
    style_body = engine_styles
    # Exclude DESIGN_TOKENS_CSS interpolation — only the Python string after import.
    # Count raw brand teal/rust in styles.py excluding the f-string token block is hard;
    # instead forbid legacy amber and require var(--cs-teal) usage.
    # Legacy amber must not appear in active token CSS or component styles.
    # The tokens module may list retired values in LEGACY_BRAND_HEX for detection.
    token_css_start = engine_tokens.find("DESIGN_TOKENS_CSS")
    active_tokens = engine_tokens[token_css_start:] if token_css_start >= 0 else engine_tokens
    legacy_hits = [h for h in LEGACY_AMBER_HEX if h in active_tokens or h in engine_styles]
    checks.append(
        CheckResult(
            "design_system:no_legacy_amber",
            not legacy_hits,
            "clean" if not legacy_hits else ",".join(legacy_hits),
            "legacy_style",
        )
    )
    checks.append(
        CheckResult(
            "design_system:uses_cs_vars",
            "var(--cs-teal" in engine_tokens and "var(--accent)" in engine_styles,
            "vars",
            "design_system",
        )
    )
    # Scattered brand hex in styles (component section): allow print literals only.
    component_css = style_body.split("REPORT_CSS", 1)[-1]
    # After print media, print hex is allowed; check screen portion roughly.
    screen = component_css.split("@media print", 1)[0]
    scattered = re.findall(r"#(?:16756a|0f5d54|a04b17|f4f6f3|111815)", screen, flags=re.I)
    checks.append(
        CheckResult(
            "design_system:no_scattered_brand_hex_in_components",
            len(scattered) == 0,
            f"count={len(scattered)}",
            "design_system",
        )
    )
    return checks, defects, consumed
