"""Future persistence-neutral ports for event-identity lookup/recording."""

from __future__ import annotations

from typing import Protocol

from codestrata_platform.community_cloud_api.event_identity.models import (
    StoredEventIdentity,
)


class EventIdentityLookup(Protocol):
    def get(self, event_key: str) -> StoredEventIdentity | None: ...


class EventIdentityRecorder(Protocol):
    def record(self, identity: StoredEventIdentity) -> None: ...


class InMemoryEventIdentityStore:
    """Test-only in-memory lookup/recorder — not a production adapter."""

    def __init__(self) -> None:
        self._items: dict[str, StoredEventIdentity] = {}

    def get(self, event_key: str) -> StoredEventIdentity | None:
        return self._items.get(event_key)

    def record(self, identity: StoredEventIdentity) -> None:
        existing = self._items.get(identity.event_key)
        if existing is not None and existing.payload_fingerprint != identity.payload_fingerprint:
            raise ValueError("conflicting_event_identity")
        self._items[identity.event_key] = identity

    def clear(self) -> None:
        self._items.clear()
