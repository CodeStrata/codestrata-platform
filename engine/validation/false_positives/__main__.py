"""Allow ``python -m validation.false_positives``."""

from __future__ import annotations

from validation.false_positives.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
