# MVP4 Dashboard Actual Long-Run Cycle Floor Audit

created_at_utc: 2026-04-30T06:46:17Z
patch_id: MVP4_DASHBOARD_ACTUAL_LONG_RUN_CYCLE_FLOOR_20260430_001

Finding:
- The dashboard long-run boundary already required 86400s duration, but it could still validate actual long-run evidence with only sparse samples across that span.
- That created a false-safe UX risk: a day-long display history with two samples could look like actual repeated runtime evidence.

Patch:
- Actual long-run validation now requires both 86400s observed duration and 2880 stable runtime samples.
- Sparse day-long histories remain ACTUAL_LONG_RUN_COLLECTING.
- Duration progress may pass separately, while cycle, evidence-window, and recovery proof remain collecting.
- A forged ACTUAL_LONG_RUN_VALIDATED boundary is blocked by the read-only dashboard validator.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
