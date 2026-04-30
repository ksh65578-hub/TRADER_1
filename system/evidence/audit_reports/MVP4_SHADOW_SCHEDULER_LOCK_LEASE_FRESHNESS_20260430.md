# MVP4 SHADOW Scheduler Lock Lease Freshness Audit

created_at_utc: 2026-04-30T04:35:48Z
patch_id: MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS_20260430_001

Finding:
- SHADOW scheduler reports validated lock ownership and positive lease duration, but did not explicitly prove that the lease was fresh.
- A stale or unproven lease could look like a clean single-writer state in operator-facing evidence, creating duplicate-writer and partial-write risk.

Patch:
- Added lock_lease_fresh and lock_lease_status to the scheduler guard report and schema.
- Stale or unproven lease freshness now blocks APPEND_SHADOW_OBSERVATION_ONLY with DUPLICATE_WRITER_RISK.
- Added regression coverage for stale lease and false-safe lease status drift.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
