"""Negative scenarios A–Z (Slice 13.6)."""

from __future__ import annotations

NEGATIVE_SCENARIOS: dict[str, str] = {
    "A": "progress starts during activation",
    "B": "progress starts during discovery",
    "C": "progress starts before consent",
    "D": "assessment creates two progress lifecycles",
    "E": "AI assessment creates second AI progress bar",
    "F": "fake percentage increments without Engine signal",
    "G": "elapsed time used as percentage",
    "H": "Findings count used as progress",
    "I": "raw stdout parsed for progress",
    "J": "repository path enters progress text",
    "K": "provider/model enters progress text",
    "L": "progress failure changes assessment result",
    "M": "telemetry failure changes progress primary outcome",
    "N": "analytics failure changes primary outcome",
    "O": "cancellation triggers second assessment",
    "P": "cancellation triggers report open",
    "Q": "duplicate cancellation kills process twice",
    "R": "progress closes twice",
    "S": "progress remains open after success",
    "T": "progress remains open after failure",
    "U": "progress remains open after cancellation",
    "V": "report missing becomes assessment failure",
    "W": "progress emits new telemetry event",
    "X": "progress adds analytics fields",
    "Y": "Slice 13.7 report-opening redesign starts",
    "Z": "report leaks paths/source/output/provider/credentials/environment/timing/timestamps",
}

PHASE_INVENTORY = [
    "running_assessment",
    "finalizing",
    "locating_report",
    "completed",
    "failed",
    "cancelled",
]
