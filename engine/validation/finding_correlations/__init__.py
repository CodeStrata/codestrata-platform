"""Internal Finding correlation diagnostics and expectations (Slice 5.12)."""

from __future__ import annotations

__all__ = ["main"]


def __getattr__(name: str):
    if name == "main":
        from validation.finding_correlations.cli import main

        return main
    raise AttributeError(name)
