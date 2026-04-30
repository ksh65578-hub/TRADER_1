# MVP4_DASHBOARD_POSITION_DETAIL_TRUTH_GUARD

generated_at_utc: 2026-04-30T18:26:26Z
status: PASS

Hidden defects handled:
- Dashboard position rows now read average_entry_price instead of showing UNKNOWN.
- Position rows now expose mark price, market value, cost basis, and unrealized PnL.
- Zero numeric values are preserved instead of being treated as missing.
- Launcher tests now write to temporary runtime roots instead of tracked dashboard runtime artifacts.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
