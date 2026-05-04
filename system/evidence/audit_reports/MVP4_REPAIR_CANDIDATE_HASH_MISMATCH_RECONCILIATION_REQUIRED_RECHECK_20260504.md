# MVP4 Repair Candidate Hash Mismatch Reconciliation Required Recheck Audit

created_at_utc: 2026-05-04T01:48:53Z
patch_id: MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK_20260504_001

Finding:
- The repair candidate rollup self-check is PASS, but the source expected rollup artifact is missing.
- The item remains blocked by REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED.
- The repair operator queue still marks one ledger-candidate item as review-ready and hash-reconciliation-required.
- Candidate current evidence usable count remains 0.

Patch:
- Added a dedicated route/evidence recheck for REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED.
- Routed next_allowed_task_class to MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK.
- Preserved post-repair, hash-mismatch, operator reconciliation, live, and scale-up blockers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no current evidence mutation
- no scale-up
