#!/usr/bin/env python3
"""Generate .generated/platform-contract-inventory.json (gitignored)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PLATFORM_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLATFORM_ROOT.parent
sys.path.insert(0, str(PLATFORM_ROOT / "src"))

from codestrata_platform.api import create_app  # noqa: E402
from codestrata_platform.api.contracts.inventory import build_contract_inventory  # noqa: E402


def main() -> int:
    app = create_app(use_memory=True)
    payload = build_contract_inventory(app)
    out = REPO_ROOT / ".generated" / "platform-contract-inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["partial"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
