"""Privacy/security safety helpers for completion reports."""

from __future__ import annotations

import json
import re
from typing import Any

FORBIDDEN_REPORT_PATTERNS = (
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"file://"),
    re.compile(r"\"timestamp\"", re.IGNORECASE),
    re.compile(r"\bgit[_\s-]?sha\b", re.IGNORECASE),
    re.compile(r"vscode\.env\.machineId"),
    re.compile(r"\"machineId\"\s*:"),
    re.compile(r"installation[_-]id\"\s*:", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
)


def report_text_is_safe(text: str) -> tuple[bool, str]:
    for pat in FORBIDDEN_REPORT_PATTERNS:
        if pat.search(text):
            return False, pat.pattern
    # Absolute-looking VSIX path leakage
    if ".vsix" in text and ("/" in text or "\\" in text):
        # Allow bare filename references without directory separators around path roots
        if re.search(r"[/\\][^\s\"]+\.vsix", text):
            return False, "vsix_path"
    return True, "safe"


def dict_to_canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
