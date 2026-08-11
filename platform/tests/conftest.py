"""Platform test collection notes.

ACTIVE_CURRENT_PLATFORM_CONTRACT vs HISTORICAL_FROZEN_CHARACTERIZATION
----------------------------------------------------------------------
Default ``pytest tests`` (private main CI) is the current shipped platform
contract: 19-route production app, public API URL constants, Insights
sentiment completeness, wired Community Data Lake ingestion flag, private
platform export.

HISTORICAL_FROZEN_CHARACTERIZATION suites that depend on missing SV.10/SV.12
frozen slice artifacts skip when those inputs are absent. They are retained
in-tree and must not gate current main.
"""
