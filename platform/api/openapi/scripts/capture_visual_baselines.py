#!/usr/bin/env python3
"""Capture structural HTML baselines for internal Platform API docs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "platform" / "src"))
sys.path.insert(0, str(ROOT / "engine" / "src"))

from fastapi.testclient import TestClient

from codestrata_platform.api.app import create_app

BASELINES = Path(__file__).resolve().parents[1] / "baselines"


def main() -> int:
    BASELINES.mkdir(parents=True, exist_ok=True)
    client = TestClient(create_app(use_memory=True))
    docs = client.get("/api/docs")
    assert docs.status_code == 200
    (BASELINES / "api-docs-shell.html").write_bytes(docs.content)
    tokens = client.get("/api/docs/static/design-tokens/tokens.css")
    assert tokens.status_code == 200
    (BASELINES / "tokens.css.sha256.txt").write_text(
        __import__("hashlib").sha256(tokens.content).hexdigest() + "\n",
        encoding="utf-8",
    )
    theme_js = client.get("/api/docs/static/js/theme.js")
    assert b"codestrata-platform-api-theme" in theme_js.content
    (BASELINES / "theme-persistence.marker").write_text(
        "localStorage key: codestrata-platform-api-theme\n"
        "modes: system|light|dark\n",
        encoding="utf-8",
    )
    print(f"Wrote baselines under {BASELINES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
