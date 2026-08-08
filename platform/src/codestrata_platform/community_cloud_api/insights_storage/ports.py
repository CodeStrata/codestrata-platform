"""S3 client port for Insights reads — list/get only."""

from __future__ import annotations

from typing import Any, Protocol


class InsightsS3ClientPort(Protocol):
    def list_objects_v2(self, **kwargs: Any) -> Any: ...

    def get_object(self, **kwargs: Any) -> Any: ...
