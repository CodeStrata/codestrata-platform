"""Minimal Flask-style app for CodeStrata sample assessments."""

from __future__ import annotations


def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    print(health())


if __name__ == "__main__":
    main()
