# MVP4 Dashboard PAPER Portfolio Current Truth UX Audit

created_at_utc: 2026-05-05T02:26:38Z
patch_id: MVP4_DASHBOARD_PAPER_PORTFOLIO_CURRENT_TRUTH_UX_20260505_002

Finding:
- Operators could read UNVERIFIED as if configured PAPER starting capital was unknown, even when the PAPER baseline was configured.

Patch:
- Kept current cash, equity, PnL, return, and positions fail-closed when current evidence is stale or missing.
- Marked configured PAPER capital as a known configuration baseline without treating it as current cash/equity.
- Added dashboard copy that states UNVERIFIED applies to current portfolio values, not the configured starting baseline.
- Changed first-screen portfolio/live labels to plain operator wording while keeping raw statuses visible for audit in the same card or detail drawer.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no current-evidence writer, live config mutation, live order, or scale-up permission added
