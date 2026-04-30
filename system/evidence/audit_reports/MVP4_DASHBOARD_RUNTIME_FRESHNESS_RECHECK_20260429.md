# MVP4 Dashboard Runtime Freshness Recheck

created_at_utc: 2026-04-29T11:05:54Z
patch_id: MVP4_DASHBOARD_RUNTIME_FRESHNESS_RECHECK_20260429_001

Findings:
- Dashboard artifacts were correct at generation time, but an open browser page did not expose enough runtime age/freshness information.
- Existing runtime dashboard_shell.json artifacts became stale after the schema gained dashboard_refresh_policy.

Patch:
- Added dashboard_refresh_policy to the dashboard shell schema and runtime shell.
- Added first-screen Dashboard Data Freshness strip with updated time, age, source freshness, and auto-refresh interval.
- Added client-side stale guard that turns the visible page stale after 300 seconds without refreshed local artifacts.
- Added local file reload every 10 seconds so a running safe monitor can update the browser view.
- Regenerated scoped runtime dashboard artifacts.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
