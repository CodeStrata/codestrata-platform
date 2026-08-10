# Engineering Intelligence Quality Review (SV.12)

**Verdict:** PASS_WITH_LIMITATIONS
**Repositories:** 22
**Dataset ID:** dataset:3da1c591fcef727714304861
**EIR Report ID:** eir:1eda169bfe4b7041265b253e
**Interpretation policy bundle:** interp-bundle:c719915c68cf94601a0e8f0b
**Website export ID:** eir-export:ca01b398f777e20ef75ea1f2

## Summary

- Defect candidates: 0
- Editorial observations: 87

## Commercial usefulness

- **CTO / VP Engineering**: strong
  - Technology estate and recurring themes are available
  - Drill-downs support follow-up repository inspection
  - Limitations must be read before generalizing risk prevalence
- **Engineering Council reviewer**: strong
  - Capability/coverage comparisons remain factual
  - Provenance and limitations support challengeability
  - No maturity/health ranking expected
- **PE technology diligence team**: limited
  - Recurring risks and technology concentration are inspectable
  - Intentionally vulnerable repos may inflate security patterns — disclosed as limitation
  - Static analysis does not prove operational outcomes
- **CodeStrata design partner**: strong
  - Cross-repository report is more than a pile of single-repo reports
  - Drill-downs enable discussion without Engine internals
  - Signal-to-noise may vary with pattern volume

## Section reviews

- **dataset_review**: ok=True — Dataset population reconciles with 22 curated pinned repositories
- **technology_distribution_review**: ok=True — Technology distribution reviewed for factual, denominator-aware insight
- **capability_comparison_review**: ok=True — Capability comparisons reviewed for absence of rank/maturity/health scores
- **assessment_head_review**: ok=True — Assessment-head distributions reviewed for non-ranking semantics
- **recurring_pattern_review**: ok=True — Recurring patterns reviewed for ≥2-repo support and dataset scope
- **modernization_observation_review**: ok=True — Modernization observations reviewed for Recommendation support and non-imperative scope
- **confidence_review**: ok=True — Confidence reviewed for non-numeric, non-accuracy presentation
- **limitation_review**: ok=True — Limitations reviewed for mandatory themes and privacy
- **repository_drilldown_review**: ok=True — Drill-downs reviewed for membership, safety, and bounded refs
- **provenance_review**: ok=True — Provenance reviewed for pattern/modernization support identities
- **wording_review**: ok=True — Wording scanned for unsupported commercial claims (disclaimer-aware)
- **usability_review**: ok=True — Qualitative usefulness assessed for four intended audiences
- **website_safe_review**: ok=True — Website-safe export reviewed for CSP, secrets, and allowlisted projection
- **special_case_review**: ok=True — 7 special-case notes; 0 ingestion rejections
- **signal_to_noise**: ok=True — Signal-to-noise qualitatively balanced

## Limitations

- SV.12 reviews one Engineering Intelligence Report built from the 22 curated v0.2.0 release-validation repositories only. It is not an industry benchmark or product-wide accuracy claim.
- SV.12 reviews one Engineering Intelligence Report built from the 22 curated v0.2.0 release-validation repositories only. It is not an industry benchmark or product-wide accuracy claim.
- Reuses SV.6 pipeline builders and SV.8 website-safe export.
- Does not overwrite platform/demo/.
- Editorial observations are separated from product defects.
- SV.11 gate verdict=PASS_WITH_LIMITATIONS
- juice-shop: intentionally vulnerable/demo posture — do not treat pattern prevalence as ordinary software risk without limitation
- nodegoat: intentionally vulnerable/demo posture — do not treat pattern prevalence as ordinary software risk without limitation
- verademo: intentionally vulnerable/demo posture — do not treat pattern prevalence as ordinary software risk without limitation
- vulnerable-app-nodejs-express: intentionally vulnerable/demo posture — do not treat pattern prevalence as ordinary software risk without limitation
- aspnetcore: submodules not initialized (SV.10); coverage limitations must remain visible
- doris: submodules not initialized (SV.10); coverage limitations must remain visible
- bookstack: Tier 3 runtime over 10m — not technical-debt severity or product inaccuracy

## Disclaimer

Results apply only to the 22 curated pinned repositories in the v0.2.0 release-validation catalog. This is not an industry benchmark or product-wide accuracy claim.

