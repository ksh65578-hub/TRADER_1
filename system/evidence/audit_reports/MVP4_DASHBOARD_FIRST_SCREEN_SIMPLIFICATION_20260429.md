# MVP4 Dashboard First-Screen Simplification

created_at_utc: 2026-04-29T09:53:31Z
patch_id: MVP4_DASHBOARD_FIRST_SCREEN_SIMPLIFICATION_20260429_001

Findings:
- The dashboard first screen was too dense for operator use.
- The user needs three things first: portfolio, whether the program is running normally, and live readiness.
- Detailed validator, source, strategy, risk, and convergence sections should remain available but should not dominate the first screen.

Patch:
- Reordered dashboard HTML so the first screen shows Portfolio Snapshot, System Status, and Live Readiness.
- Collapsed detailed status, evidence, validator, strategy, risk, convergence, and source sections below the first screen.
- Preserved display-only truth wording and all live/order/scale blockers.
- Added layout tests that reject the previous always-open detail view.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
