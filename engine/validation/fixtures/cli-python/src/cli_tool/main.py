"""Minimal argparse CLI (no web framework)."""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validation CLI stub")
    parser.add_argument("--name", default="world", help="Name to greet")
    args = parser.parse_args(argv)
    print(f"hello {args.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
