# MVP4 Dashboard Stability Trends UX Audit

created_at_utc: 2026-04-28T23:24:12Z
patch_id: MVP4_DASHBOARD_STABILITY_TRENDS_UX_20260429_001

Findings:
- Operators could see heartbeat status, but not a compact stability breakdown for heartbeat age, source freshness, resource pressure, event latency, queue backlog, or rate-limit pressure.
- A future dashboard could claim stable status while a stability metric is stale or degraded unless validator logic blocks false-stable display.
- Historical trend evidence does not exist yet, so any long-run trend wording would be misleading.

Patch:
- Added stability_trends to the read-only dashboard shell and schema.
- Rendered Stability Trends on the first screen with green/yellow/red semantics.
- Added negative tests for live permission drift, execution truth drift, and false stable status.
- Added a WARN fixture for rate-limit pressure.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
