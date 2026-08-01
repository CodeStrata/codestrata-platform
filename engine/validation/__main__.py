"""Allow ``python -m validation`` to list help via run_validation."""

from __future__ import annotations

from validation.run_validation import main

if __name__ == "__main__":
    raise SystemExit(main())
