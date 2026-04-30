# MVP4 Dashboard Recent Events UX Audit

created_at_utc: 2026-04-28T23:15:16Z
patch_id: MVP4_DASHBOARD_RECENT_EVENTS_UX_20260429_001

Findings:
- Dashboard did not show a compact recent activity timeline, so operators had to infer what just happened from separate panels.
- Recent NO_TRADE context needed a display-only guard so it could not be interpreted as execution truth.
- Text-level order-control wording was removed from the recent activity explanation.

Patch:
- Added recent_events to dashboard shell and schema.
- Rendered Recent Activity on the first screen.
- Added negative tests for recent event live permission drift, execution truth claims, and missing NO_TRADE event.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
