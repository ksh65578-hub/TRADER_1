# MVP4_PAPER_PORTFOLIO_POSITION_ROLLUP_GUARD

generated_at_utc: 2026-04-30T19:22:40Z
status: PASS

Hidden defects handled:
- PAPER portfolio schema now requires strict position detail fields.
- Position validation now reconciles market value, cost basis, unrealized PnL, and rollup totals.
- Runtime cycle validation now fails closed when nested position detail is tampered.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
