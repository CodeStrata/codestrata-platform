"""Assessment input preparation tests (offline)."""

from __future__ import annotations

import pytest

from verification.engineering_intelligence.assessment_inputs import prepare_catalog_assessments
from verification.engineering_intelligence.contract import PREFERRED_FIVE_LANGUAGE_SUBSET


def test_prepare_requires_cache_or_network(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        prepare_catalog_assessments(
            work_root=tmp_path,
            repository_ids=PREFERRED_FIVE_LANGUAGE_SUBSET[:1],
            with_catalog_network=False,
            reuse_cache=True,
        )
