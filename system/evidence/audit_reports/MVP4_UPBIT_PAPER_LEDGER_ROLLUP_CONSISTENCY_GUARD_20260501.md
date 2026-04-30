# MVP4 Upbit PAPER Ledger Rollup Consistency Guard

created_at_utc: 2026-04-30T17:17:14Z
patch_id: MVP4_UPBIT_PAPER_LEDGER_ROLLUP_CONSISTENCY_GUARD_20260501_001

Finding:
- PAPER ledger rollup validation could accept hash-recomputed reports with cross-scope portfolio snapshots, inconsistent filled counts, or escaped artifact paths.

Patch:
- Enforced exact rollup/portfolio scope match.
- Enforced filled-order/position count consistency and latest ledger head presence.
- Blocked artifact paths outside the UPBIT/KRW_SPOT/PAPER ledger namespace.
- Added negative tests and validator coverage.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential use
- no exchange private API call
- no live order path enabled
