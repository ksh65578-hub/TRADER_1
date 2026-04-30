# MVP4_SUMMARY_POSITION_ROLLUP_GUARD

generated_at_utc: 2026-04-30T19:45:36Z
status: PASS

Hidden defects handled:
- Dashboard summary schema now requires strict PAPER position detail fields.
- Summary validation now reconciles per-position market value and unrealized PnL.
- Top-level summary rollups must match position-row sums before dashboard display truth passes.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
