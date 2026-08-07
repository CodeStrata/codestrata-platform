"""Negative scenarios A–Z (Slice 13.5)."""

from __future__ import annotations

NEGATIVE_SCENARIOS: dict[str, str] = {
    "A": "assessment runs during activation",
    "B": "assessment runs with no workspace",
    "C": "assessment runs before initialization",
    "D": "assessment runs with invalid config",
    "E": "assessment runs with incompatible CLI",
    "F": "telemetry prompts before readiness checks",
    "G": "standard assessment invokes CLI twice",
    "H": "AI assessment invokes CLI twice",
    "I": "AI assessment silently falls back to standard",
    "J": "assessment silently invokes scan",
    "K": "extension interprets finding count as success/failure",
    "L": "telemetry failure changes CLI result",
    "M": "analytics failure changes CLI result",
    "N": "progress failure changes CLI result",
    "O": "report-open failure changes assessment result",
    "P": "cancellation triggers retry",
    "Q": "successful CLI with missing report treated as full report success",
    "R": "source file modified",
    "S": "config file modified",
    "T": ".git modified",
    "U": "extension sends source over network",
    "V": "provider credential enters extension diagnostics",
    "W": "stdout/stderr enters public result",
    "X": "product invocation count > 1",
    "Y": "Slice 13.6 progress redesign starts",
    "Z": "report leaks paths/source/config/output/environment/provider/credentials/timestamps",
}
