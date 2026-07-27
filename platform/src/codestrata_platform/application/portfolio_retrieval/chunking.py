"""Portfolio retrieval chunking policy exports.

Document/chunk construction lives in ``document_builder``. This module keeps the
package layout aligned with Engineering Retrieval's ``chunking`` module while
reusing the shared portfolio chunking policy.
"""

from __future__ import annotations

from codestrata_platform.application.portfolio_retrieval.document_builder import (
    PortfolioRetrievalDocumentBuilder,
)
from codestrata_platform.application.portfolio_retrieval.policies import (
    PORTFOLIO_CHUNKING_POLICY_VERSION,
    DefaultPortfolioChunkingPolicy,
)

# Alias matching the phase brief naming.
PortfolioChunkingPolicy = DefaultPortfolioChunkingPolicy

__all__ = [
    "DefaultPortfolioChunkingPolicy",
    "PORTFOLIO_CHUNKING_POLICY_VERSION",
    "PortfolioChunkingPolicy",
    "PortfolioRetrievalDocumentBuilder",
]
