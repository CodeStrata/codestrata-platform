#!/usr/bin/env python3
"""Showcase utility: fetch + assess a pinned real-world example (network).

Thin monorepo-root wrapper around
``examples/real-world/scripts/run_showcase.py``.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "real-world"
    / "scripts"
    / "run_showcase.py"
)

if __name__ == "__main__":
    sys.argv[0] = str(SCRIPT)
    runpy.run_path(str(SCRIPT), run_name="__main__")
