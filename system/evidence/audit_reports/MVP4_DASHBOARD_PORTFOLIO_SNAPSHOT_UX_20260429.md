# MVP4 Dashboard Portfolio Snapshot UX Audit

created_at_utc: 2026-04-28T22:24:36Z
patch_id: MVP4_DASHBOARD_PORTFOLIO_SNAPSHOT_UX_20260429_001

Finding:
- The dashboard showed safety and blocker state, but did not expose operator-facing cash, equity, open positions, or return. This created a user misjudgment risk because the first screen did not answer whether portfolio state was known, missing, or stale.

Patch:
- Added a first-screen portfolio snapshot section with Cash, Equity, Open Positions, and Return cards.
- Added read-only schema fields for the portfolio snapshot.
- Added negative tests that block portfolio execution-truth claims, portfolio live permission drift, and fresh-looking values while the portfolio remains unverified.
- Kept all displayed portfolio values UNVERIFIED until a verified paper ledger or read-only account snapshot exists.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
