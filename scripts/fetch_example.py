#!/usr/bin/env python3
"""Showcase utility: fetch a pinned real-world example.

Thin monorepo-root wrapper around
``examples/real-world/scripts/fetch_example.py``.
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
    / "fetch_example.py"
)

if __name__ == "__main__":
    sys.argv[0] = str(SCRIPT)
    runpy.run_path(str(SCRIPT), run_name="__main__")
