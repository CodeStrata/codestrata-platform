"""SHA-256 helpers."""

from __future__ import annotations

import hashlib
from typing import Mapping


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_sha256sums(checksums: Mapping[str, str]) -> str:
    """GNU-style SHA256SUMS sorted by relative path. No absolute paths."""

    lines = [f"{checksums[path]}  {path}" for path in sorted(checksums)]
    return "\n".join(lines) + ("\n" if lines else "")
