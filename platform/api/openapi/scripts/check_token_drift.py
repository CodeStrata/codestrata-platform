#!/usr/bin/env python3
"""Fail when Platform API Swagger tokens drift from Community docs tokens."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
COMMUNITY = ROOT / "docs" / "public" / "design-tokens" / "tokens.css"
PLATFORM = (
    ROOT
    / "platform"
    / "api"
    / "openapi"
    / "swagger"
    / "design-tokens"
    / "tokens.css"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not COMMUNITY.is_file() or not PLATFORM.is_file():
        print("missing token files", file=sys.stderr)
        return 1
    if _sha(COMMUNITY) != _sha(PLATFORM):
        print(
            "Design token drift: sync with\n"
            "  cp docs/public/design-tokens/tokens.css "
            "platform/api/openapi/swagger/design-tokens/tokens.css",
            file=sys.stderr,
        )
        return 1
    print("Design tokens in sync with Community docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
