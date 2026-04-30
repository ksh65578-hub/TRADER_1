# MVP4 Runtime Write Lock Live Owner Recheck Audit

created_at_utc: 2026-04-29T08:29:51Z
patch_id: MVP4_RUNTIME_WRITE_LOCK_LIVE_OWNER_RECHECK_20260429_001

Finding:
- The runtime writer lock treated a lock as stale using only file age. A long-running safe monitor/dashboard refresh could exceed the stale age, allowing another process to remove a still-owned lock and create duplicate same-session writers.

Patch:
- Runtime write lock now parses the owner PID from the lock token.
- A stale-looking lock is only removed when its owner process is no longer running.
- Tests cover both paths: live-owner stale lock remains blocking, dead-owner stale lock recovers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
