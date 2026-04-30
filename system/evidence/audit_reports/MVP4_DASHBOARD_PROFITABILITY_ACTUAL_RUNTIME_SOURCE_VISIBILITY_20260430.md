# MVP4 Dashboard Profitability Actual Runtime Source Visibility Audit

created_at_utc: 2026-04-30T07:28:09Z
patch_id: MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY_20260430_001

Finding:
- Paper/shadow evidence validation requires a validated non-live persistent runtime source before any long-run claim, but the dashboard profitability maturity panel did not expose that source status directly.
- This could make scorecard input look more complete than it is, increasing operator UX risk and optimizer/convergence false-safe risk.
- Browser inspection also showed narrow detail cards could clip long status strings instead of wrapping them, making the user-facing blocker harder to read.

Patch:
- Added actual_runtime_source_status, actual_runtime_source_count, actual_runtime_source_summary, long_run_evidence_eligible, and long_run_blocker_code to the dashboard profitability maturity projection and schema.
- Added dashboard validator checks that block long-run eligibility without validated non-live runtime source evidence.
- Added negative dashboard tests for false long-run eligibility and validated-runtime status without source ids.
- Hardened dashboard CSS so long status tokens, detail cards, readiness rows, and evidence requirement text wrap within their cards on narrow viewports.
- Regenerated UPBIT and BINANCE PAPER dashboard artifacts through safe launcher paths only.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
