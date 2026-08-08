"""Determinism checks for Assessment HTML rendering."""

from __future__ import annotations

from pathlib import Path

from verification.assessment_report_redesign.models import CheckResult, Defect
from verification.assessment_report_redesign.renderer import _render_sample


def check_determinism(tmp_path: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    a = _render_sample(tmp_path / "a")
    b = _render_sample(tmp_path / "b")
    # Repository path in title/meta may differ by tmp folder name; normalize by
    # comparing structural token presence and byte equality of CSS/token block.
    css_a = a.split("<style>", 1)[-1].split("</style>", 1)[0]
    css_b = b.split("<style>", 1)[-1].split("</style>", 1)[0]
    ok_css = css_a == css_b
    checks.append(
        CheckResult("determinism:css_identical", ok_css, "css", "determinism")
    )
    # Full HTML may include tmp repository names — compare after stripping path-like runs.
    def _scrub(html: str) -> str:
        # Remove title repository segment variance by keeping structure markers.
        return "\n".join(
            line
            for line in html.splitlines()
            if "tmp" not in line.lower() and "/var/" not in line and "/Users/" not in line
        )

    ok_struct = _scrub(a) == _scrub(b)
    checks.append(
        CheckResult(
            "determinism:structure_stable",
            ok_struct,
            "structure",
            "determinism",
        )
    )
    checks.append(
        CheckResult(
            "determinism:no_uuid_noise",
            "uuid" not in css_a.lower(),
            "no_uuid",
            "determinism",
        )
    )
    if not ok_css:
        defects.append(
            Defect("determinism defect", "css", "identical", "divergent")
        )
    return checks, defects
