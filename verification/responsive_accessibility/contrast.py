"""WCAG relative-luminance contrast math and token pair evaluation.

The ratio implementation follows WCAG 2.x: sRGB channels are linearised, combined
into relative luminance, and compared as ``(L_lighter + 0.05) / (L_darker + 0.05)``.
"""

from __future__ import annotations

from verification.responsive_accessibility.contract import (
    LARGE_TEXT_RATIO,
    NON_TEXT_RATIO,
    NORMAL_TEXT_RATIO,
)
from verification.responsive_accessibility.models import CheckResult, ContrastMeasurement, Defect

_REQUIRED_BY_KIND = {
    "normal_text": NORMAL_TEXT_RATIO,
    "large_text": LARGE_TEXT_RATIO,
    "non_text_essential": NON_TEXT_RATIO,
    "focus_indicator": NON_TEXT_RATIO,
}


def parse_hex(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(channel * 2 for channel in text)
    if len(text) != 6:
        raise ValueError(f"unsupported colour literal: {value!r}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def _linearise(channel: int) -> float:
    ratio = channel / 255.0
    if ratio <= 0.04045:
        return ratio / 12.92
    return ((ratio + 0.055) / 1.055) ** 2.4


def relative_luminance(value: str) -> float:
    red, green, blue = parse_hex(value)
    return (
        0.2126 * _linearise(red) + 0.7152 * _linearise(green) + 0.0722 * _linearise(blue)
    )


def contrast_ratio(foreground: str, background: str) -> float:
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def required_ratio(kind: str) -> float:
    return _REQUIRED_BY_KIND.get(kind, NORMAL_TEXT_RATIO)


def measure_pairs(
    contract: dict, colors: dict[str, str]
) -> tuple[list[ContrastMeasurement], list[str]]:
    """Measure every required pair declared by the accessibility contract."""

    measurements: list[ContrastMeasurement] = []
    unknown: list[str] = []
    required = contract.get("contrast", {}).get("required_pairs", {})
    for theme in sorted(required):
        for pair in required[theme]:
            foreground = colors.get(pair["foreground"])
            background = colors.get(pair["background"])
            if foreground is None or background is None:
                unknown.append(f"{theme}:{pair['id']}")
                continue
            kind = pair.get("kind", "normal_text")
            measurements.append(
                ContrastMeasurement(
                    pair_id=pair["id"],
                    theme=theme,
                    kind=kind,
                    ratio=contrast_ratio(foreground, background),
                    required=required_ratio(kind),
                )
            )
    return measurements, unknown


def check_contrast(
    contract: dict, colors: dict[str, str]
) -> tuple[list[CheckResult], list[Defect], list[ContrastMeasurement]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    measurements, unknown = measure_pairs(contract, colors)

    checks.append(
        CheckResult(
            "contrast:all_pairs_resolvable",
            not unknown,
            "resolved" if not unknown else ",".join(sorted(unknown)),
            "contrast",
        )
    )
    checks.append(
        CheckResult(
            "contrast:pairs_declared",
            len(measurements) >= 40,
            f"{len(measurements)}",
            "contrast",
        )
    )

    for theme in ("light", "dark", "print"):
        subset = [m for m in measurements if m.theme == theme]
        checks.append(
            CheckResult(
                f"contrast:theme_covered:{theme}",
                bool(subset),
                f"{len(subset)}",
                "contrast",
            )
        )

    for measurement in measurements:
        checks.append(
            CheckResult(
                f"contrast:{measurement.theme}:{measurement.pair_id}",
                measurement.ok,
                f"{measurement.ratio:.2f}>={measurement.required}",
                "contrast",
            )
        )
        if not measurement.ok:
            defects.append(
                Defect(
                    "contrast",
                    f"{measurement.theme} pair {measurement.pair_id} measures "
                    f"{measurement.ratio:.2f}:1 against a {measurement.required}:1 target",
                )
            )

    # Self-test of the ratio implementation against known reference values.
    checks.append(
        CheckResult(
            "contrast:math_reference_black_white",
            abs(contrast_ratio("#000000", "#ffffff") - 21.0) < 0.01,
            "21.0",
            "contrast",
        )
    )
    checks.append(
        CheckResult(
            "contrast:math_reference_identity",
            abs(contrast_ratio("#16756a", "#16756a") - 1.0) < 0.001,
            "1.0",
            "contrast",
        )
    )
    checks.append(
        CheckResult(
            "contrast:math_symmetric",
            abs(contrast_ratio("#111815", "#f4f6f3") - contrast_ratio("#f4f6f3", "#111815"))
            < 1e-9,
            "symmetric",
            "contrast",
        )
    )
    return checks, defects, measurements
