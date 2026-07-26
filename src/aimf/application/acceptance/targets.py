"""Dogfood repository targets for MVP acceptance."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

ACCEPTANCE_TARGETS: tuple[tuple[str, Path], ...] = (
    ("codestrata", ROOT),
    ("spring-petclinic", ROOT / ".aimf" / "workspace" / "spring-petclinic"),
    ("synthetic-multilang", ROOT / "examples" / "sample-js-app"),
)

PREDEFINED_QUESTIONS: tuple[str, ...] = (
    "How is the repository architecture organized?",
    "What are the highest-severity security findings?",
    "Which dependencies create modernization risk?",
    "Where is authentication implemented?",
    "What testing limitations were identified?",
    "What performance risks exist?",
    "How is cloud configuration handled?",
    "What technical-debt recommendations were generated?",
)

# Live onboard creates a new scan_id each run; treat as volatile for determinism.
LIVE_DETERMINISM_EXTRA_PATHS: tuple[str, ...] = ("manifest.scan_id",)
