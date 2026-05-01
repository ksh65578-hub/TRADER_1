# MVP4 Upbit PAPER Blocked Repair Reason Rollup Audit

created_at_utc: 2026-05-01T02:04:38Z
patch_id: MVP4_UPBIT_PAPER_BLOCKED_REPAIR_REASON_ROLLUP_20260501_001

Finding:
- Blocked regenerated replacements were excluded from current evidence, but the report did not show whether each item was blocked by ledger rollup, recovery guard, or runtime cycle reconciliation.

Patch:
- Added per-item blocked repair reason codes, summaries, ledger/recovery/cycle status, and operator repair action.
- Added aggregate blocked_repair_reason_counts to the post-regeneration report schema and validator.
- Kept blocked repairs excluded from current evidence.

Runtime summary:
- post_reconciliation_status: BLOCKED
- regenerated_current_blocked_reconciliation_count: 6
- blocked_repair_reason_counts: [{"reason_code": "LEDGER_ROLLUP_BLOCKED", "count": 6}, {"reason_code": "LEDGER_ROLLUP_RECONCILIATION_REQUIRED", "count": 6}, {"reason_code": "LOOP_RECONCILIATION_REQUIRED", "count": 6}, {"reason_code": "LOOP_STATUS_BLOCKED", "count": 6}, {"reason_code": "PAPER_RUNTIME_RESUME_BLOCKED", "count": 1}, {"reason_code": "PARTIAL_WRITE_RECOVERY_REQUIRED", "count": 1}, {"reason_code": "RECOVERY_GUARD_BLOCKED", "count": 1}]
- current_evidence_usable_count: 10
- excluded_from_current_evidence_count: 6

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
