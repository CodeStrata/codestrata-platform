"""Artifact checksum helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_sha256sums(files: list[Path], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for path in sorted(files, key=lambda item: item.name):
        if not path.is_file():
            continue
        digest = sha256_file(path)
        lines.append(f"{digest}  {path.name}")
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return destination


def verify_sha256sums(sums_path: Path, directory: Path) -> list[str]:
    errors: list[str] = []
    if not sums_path.is_file():
        return [f"missing {sums_path}"]
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            errors.append(f"malformed line: {line!r}")
            continue
        expected, name = parts[0], parts[-1]
        path = directory / name
        if not path.is_file():
            errors.append(f"missing artifact: {name}")
            continue
        actual = sha256_file(path)
        if actual != expected:
            errors.append(f"checksum mismatch: {name}")
    return errors
