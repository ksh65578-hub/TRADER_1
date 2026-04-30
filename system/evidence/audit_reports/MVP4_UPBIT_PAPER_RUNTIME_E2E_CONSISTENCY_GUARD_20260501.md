# MVP4 Upbit PAPER Runtime E2E Consistency Guard

created_at_utc: 2026-04-30T17:05:01Z
patch_id: MVP4_UPBIT_PAPER_RUNTIME_E2E_CONSISTENCY_GUARD_20260501_001

Finding:
- Persistent PAPER loop reports could false-pass an inconsistent actual_paper_runtime_executed flag, duplicated cycle identity/hash evidence, or cross-namespace artifact paths after report mutation.

Patch:
- Tightened persistent loop validation for execution flag/count consistency.
- Blocked duplicate collector ids, cycle ids, collection hashes, and runtime hashes.
- Blocked cycle artifact paths outside UPBIT/KRW_SPOT/PAPER session namespace.
- Closed nested cycle_results schema shape.
- Added negative tests and validator coverage.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential use
- no exchange private API call
- no live order path enabled
