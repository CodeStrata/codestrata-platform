"""CLI entry point for Slice 14.9 verification."""

from __future__ import annotations

import sys

from verification.report_navigation_ia.runner import main

if __name__ == "__main__":
    sys.exit(main())
