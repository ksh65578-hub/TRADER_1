# MVP4 Dashboard Portfolio Detail Layout

created_at_utc: 2026-04-29T10:09:58Z
patch_id: MVP4_DASHBOARD_PORTFOLIO_DETAIL_LAYOUT_20260429_001

Findings:
- First-screen portfolio was too sparse for operator review.
- PnL, held positions, and entry candidates were not visible enough.
- Detail tables needed a narrow-screen overflow guard.

Patch:
- Added locked cash, realized PnL, unrealized PnL, total PnL, entry candidates, and compact first-screen position/candidate lists.
- Wrapped detail tables in horizontal scroll containers to prevent clipping.
- Replaced non-ASCII separators with plain ASCII separators in dashboard text.
- Preserved collapsed detail sections, display-only wording, and all live/order/scale blockers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
