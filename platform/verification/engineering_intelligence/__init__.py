"""SV.6 Engineering Intelligence Pipeline Verification (Platform-only).

Not part of the Platform runtime distribution package.
"""

from __future__ import annotations

from verification.engineering_intelligence.contract import (
    ENGINEERING_INTELLIGENCE_VERIFICATION_ID,
    ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION,
)
from verification.engineering_intelligence.runner import (
    run_engineering_intelligence_verification,
)

__all__ = [
    "ENGINEERING_INTELLIGENCE_VERIFICATION_ID",
    "ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION",
    "run_engineering_intelligence_verification",
]
