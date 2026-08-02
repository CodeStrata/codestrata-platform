"""Allow ``python -m validation.false_negatives``."""

from __future__ import annotations

from validation.false_negatives.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
