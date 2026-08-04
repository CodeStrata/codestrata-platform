"""Permanent catalog resolution tests."""

from __future__ import annotations

from verification.engineering_intelligence.catalog import (
    load_permanent_catalog,
    resolve_subset,
)
from verification.engineering_intelligence.contract import (
    CATALOG_RELATIVE_PATH,
    PREFERRED_FIVE_LANGUAGE_SUBSET,
)


def test_load_permanent_catalog() -> None:
    catalog = load_permanent_catalog()
    assert catalog.schema_name == "codestrata-repository-catalog"
    assert catalog.relative_path == CATALOG_RELATIVE_PATH
    assert catalog.catalog_id
    assert catalog.repositories


def test_preferred_subset_resolves_pinned_commits() -> None:
    catalog = load_permanent_catalog()
    entries = resolve_subset(catalog, repository_ids=PREFERRED_FIVE_LANGUAGE_SUBSET)
    assert [e.repository_id for e in entries] == list(PREFERRED_FIVE_LANGUAGE_SUBSET)
    for entry in entries:
        assert entry.qualified_revision.revision_type == "commit"
        assert len(entry.qualified_revision.value) == 40
