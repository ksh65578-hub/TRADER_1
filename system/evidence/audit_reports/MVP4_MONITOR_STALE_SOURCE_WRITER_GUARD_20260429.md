# MVP4 Monitor Stale Source Writer Guard

generated_at_utc: 2026-04-29T02:12:23Z

Finding:
- Long-running PAPER launcher monitor processes can keep an older in-memory source tree and overwrite dashboard runtime artifacts after a newer code/schema patch.

Patch:
- `refresh_launcher_monitor_artifacts` now compares the launcher report source_tree_hash with the current source tree hash.
- If the source identity changed, it returns a BLOCKED heartbeat with SOURCE_IDENTITY_MISMATCH and does not refresh dashboard artifacts.
- Added a negative test proving stale monitor writers do not overwrite the existing dashboard shell.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
