# MVP4 Long-Run Runtime Resource Guard Audit

created_at_utc: 2026-04-28T23:49:53Z
patch_id: MVP4_LONG_RUN_STABILITY_RESOURCE_GUARD_20260429_001

Findings:
- Long-running launchers could silently accumulate runtime files or leave temp write files without a dedicated dashboard metric.
- A stale runtime write lock was only handled by the lock acquisition path, not separately exposed as operator-visible resource pressure.
- Dashboard stability showed resource health, but not artifact/disk-growth pressure as its own first-screen signal.

Patch:
- Added runtime_resource_pressure inspection for runtime artifact count, byte count, temp write files, and stale write locks.
- Wired runtime pressure into launcher heartbeat disk and queue_backlog components before dashboard generation.
- Added Runtime artifact pressure to dashboard Stability Trends with green/yellow/red status rules.
- Added runtime_resource_pressure_validator and negative fixtures for growth warning and stale lock hard block.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
