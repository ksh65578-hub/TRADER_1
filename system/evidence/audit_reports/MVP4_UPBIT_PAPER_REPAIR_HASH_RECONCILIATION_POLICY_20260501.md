# MVP4 Upbit PAPER Repair Hash Reconciliation Policy Audit

created_at_utc: 2026-05-01T11:34:43Z
patch_id: MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY_20260501_001

Finding:
- Repair candidates exposed only pass/mismatch counts. The runtime evidence did not show whether the source expected rollup artifact existed or whether candidate hashes were recomputed and self-checked.

Patch:
- Added strict hash reconciliation evidence to ledger repair and post-repair reconciliation reports.
- Added schema, validator, and test checks for candidate hash self-check, expected artifact availability, status counts, and operator-action counts.
- Kept every repair candidate blocked from current evidence.

Runtime summary:
- ledger_repair_status: BLOCKED
- post_repair_reconciliation_status: BLOCKED
- repair_candidate_count: 1
- hash_reconciliation_operator_action_required_count: 1
- candidate_current_evidence_usable_count: 0
- primary_blocker_code: POST_REPAIR_RECONCILIATION_REQUIRED

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
