# MVP4 Dashboard Paper Portfolio Values Audit

created_at_utc: 2026-04-28T22:37:01Z
patch_id: MVP4_DASHBOARD_PAPER_PORTFOLIO_VALUES_20260429_001

Finding:
- The dashboard displayed Cash, Equity, Open Positions, and Return cards, but values were still UNVERIFIED for PAPER runs.
- This was a user workflow defect: PAPER operators could not distinguish a running simulated account from missing portfolio evidence.

Patch:
- Added PAPER-only paper_portfolio_snapshot schema and runtime builder.
- Connected paper_portfolio_snapshot to summary portfolio fields.
- Updated the read-only dashboard to show verified simulated PAPER values while clearly labeling them as not exchange balances.
- Added negative tests for live flag drift, unsupported scope, arithmetic tamper, unverified fresh-looking values, and non-PAPER verified display.
- Updated launchers to write paper_portfolio_snapshot.json for PAPER sessions only.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
