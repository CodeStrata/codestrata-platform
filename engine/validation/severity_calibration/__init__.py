"""Internal Finding severity calibration diagnostics (Slice 5.13)."""

from __future__ import annotations

__all__ = ["main"]


def __getattr__(name: str):
    if name == "main":
        from validation.severity_calibration.cli import main

        return main
    raise AttributeError(name)
