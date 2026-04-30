# MVP4 Stale Heartbeat Recovery Guidance Audit

created_at_utc: 2026-04-28T23:59:13Z
patch_id: MVP4_STALE_HEARTBEAT_RECOVERY_GUIDANCE_20260429_001

Findings:
- The read-only dashboard emitted seven stability metrics, but its schema still capped the metric list at six.
- Stale heartbeat recovery guidance was not a first-class dashboard field.
- Console heartbeat output could display a stale heartbeat artifact as RUNNING_SAFE_MODE when only the stored heartbeat_status was inspected.

Patch:
- Corrected read_only_dashboard_shell metric cardinality to seven.
- Added operation_status.recovery_hint and rendered it on the first screen.
- Added console heartbeat stale-age detection with LATENCY_TTL_EXPIRED blocker and recovery guidance.
- Strengthened validator and tests for schema/runtime metric count, recovery guidance, and stale console heartbeat negative case.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
