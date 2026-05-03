# MVP4 Upbit PAPER Ledger Idempotency Runtime Depth Recheck

created_at_utc: 2026-05-03T13:22:09Z
patch_id: MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK_20260503_001

Finding:
- Ledger idempotency evidence recomputed rollup and JSONL counts, but did not require the rollup ledger head cycle to be bound to the current persistent-loop runtime-depth summary.

Patch:
- Added persistent-loop source hash and validation fields to the ledger idempotency evidence report.
- Required ledger_head_cycle_id to exist in persistent loop cycle_results with public market data input, matching source/runtime public hash, canonical event depth, feature hash, and strategy/regime/cost linkage hash.
- Added negative tests for missing persistent loop evidence, runtime-depth hash mismatch, and linkage live permission mutation.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
