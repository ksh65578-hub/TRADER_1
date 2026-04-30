# MVP4 Dashboard Recovery Guard Visibility Audit

created_at_utc: 2026-04-30T10:56:24Z
patch_id: MVP4_DASHBOARD_RECOVERY_GUARD_VISIBILITY_20260430_001

Findings:
- Hidden issue: PAPER runtime recovery guard reports could be produced by the runtime, but the operator dashboard did not surface them on the first screen or in details.
- Hidden issue: after adding the new dashboard field, stale dashboard_shell artifacts failed runtime schema instance validation until launcher dashboard bundles were regenerated.
- UX risk: users could see a fresh heartbeat and assume the PAPER runtime can resume, even when local JSONL recovery guard evidence is stale, blocked, invalid, or not loaded.

Patch:
- Added PAPER runtime recovery status to the dashboard operation panel and detailed status drawer.
- Added schema validation for the new display-only recovery guard status.
- Added launcher wiring for a canonical session-scoped recovery guard report path.
- Added negative dashboard tests for partial-write blockers and live-permission mutation attempts.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
