"""Order-independence utilities for collections and EI rebuilds."""

from __future__ import annotations

import random
from collections.abc import Sequence
from typing import Any, TypeVar

T = TypeVar("T")


def reversed_list(items: Sequence[T]) -> list[T]:
    return list(reversed(items))


def shuffled_deterministic(items: Sequence[T], *, seed: int = 15) -> list[T]:
    out = list(items)
    rng = random.Random(seed)
    rng.shuffle(out)
    return out


def group_by_language(assessments: Sequence[Any]) -> list[Any]:
    return sorted(
        assessments,
        key=lambda a: (
            getattr(a, "language_group", "") or "",
            getattr(a, "repository_id", ""),
        ),
    )


def group_by_tier_proxy(assessments: Sequence[Any]) -> list[Any]:
    return sorted(
        assessments,
        key=lambda a: (
            len(getattr(a, "repository_id", "") or ""),
            getattr(a, "repository_id", ""),
        ),
    )
