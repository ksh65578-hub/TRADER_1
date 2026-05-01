# MVP4 Windows Restart Recovery Artifact Path Guard

created_at_utc: 2026-05-01T13:28:16Z
patch_id: MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD_20260501_001

Patch:
- restart_recovery_report now records Windows path recovery, atomic write recovery, partial-write recovery, stale-lock recovery, and recovery artifact paths.
- Restart recovery PASS requires all recovery checks to be true.
- Recovery artifact paths must be relative POSIX paths with no Windows drive prefix, backslash, absolute path, empty segment, dot segment, or parent traversal.
- Negative fixtures cover drive paths, backslashes, parent traversal, missing partial-write evidence, and empty artifact paths.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
