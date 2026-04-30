# MVP4 Long-Run Evidence Threshold Floor Audit

created_at_utc: 2026-04-30T06:05:50Z
patch_id: MVP4_LONG_RUN_EVIDENCE_THRESHOLD_FLOOR_20260430_001

Finding:
- Actual runtime blocker and runtime orchestration reports could reject false long-run claims, but low threshold floors were not explicitly blocked.
- A bad or mutated artifact could lower required runtime/cycle/window counts and make short-window evidence easier to misread.

Patch:
- Enforced minimum runtime window floor: 86400 seconds.
- Enforced minimum actual cycle count floor: 2880 cycles.
- Enforced orchestration evidence window floor: 20 windows.
- Added negative tests for weakened threshold reports.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
