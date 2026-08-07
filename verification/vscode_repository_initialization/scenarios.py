"""Negative scenarios A–Z (Slice 13.4) — expected all false / blocked."""

from __future__ import annotations

NEGATIVE_SCENARIOS: dict[str, str] = {
    "A": "initialization runs during activation",
    "B": "initialization runs automatically after installation guidance",
    "C": "initialization runs with no workspace",
    "D": "initialization runs with incompatible CLI",
    "E": "initialization prompts telemetry",
    "F": "initialization creates analytics",
    "G": "initialization runs assessment",
    "H": "initialization invokes AI",
    "I": "initialization opens report",
    "J": "extension writes config without Engine",
    "K": "init CLI invoked twice",
    "L": "existing config silently overwritten",
    "M": "invalid config deleted",
    "N": "invalid config silently repaired",
    "O": "source file modified",
    "P": "package/build file modified unexpectedly",
    "Q": ".git modified",
    "R": "network access occurs",
    "S": "Engine success without initialized state reported as success",
    "T": "cancellation becomes success",
    "U": "raw stdout/stderr enters result",
    "V": "repository/config/CLI path enters diagnostics",
    "W": "repeated initialization corrupts config",
    "X": "CLI discovery failure still invokes init",
    "Y": "Slice 13.5 assessment redesign begins",
    "Z": "verification report leaks secrets/paths/timestamps",
}
