# MVP4 Actual Runtime Harness Threshold Floor Audit

created_at_utc: 2026-04-30T06:17:23Z
patch_id: MVP4_ACTUAL_RUNTIME_HARNESS_THRESHOLD_FLOOR_20260430_001

Finding:
- Actual runtime blocker and orchestration reports enforced 86400-second and 2880-cycle long-run floors.
- The short-window actual runtime harness still allowed lower configured threshold floors above the short-window maximum, so a mutated harness report could weaken the long-run threshold without being blocked.

Patch:
- Enforced minimum runtime window floor: 86400 seconds.
- Enforced minimum actual cycle count floor: 2880 cycles.
- Tightened the harness report schema to the same floors.
- Added a negative test for weakened harness threshold reports.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
