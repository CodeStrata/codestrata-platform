"""Infrastructure repository export (Slice 12.6).

Deterministic allowlist-driven export for the future private
``codestrata-infrastructure`` repository. Performs no Git, AWS, OpenTofu,
or deployment operations.
"""

from __future__ import annotations

EXPORTER_ID = "infrastructure-repository-exporter"
EXPORTER_VERSION = "1.0.0"

__all__ = ["EXPORTER_ID", "EXPORTER_VERSION"]
