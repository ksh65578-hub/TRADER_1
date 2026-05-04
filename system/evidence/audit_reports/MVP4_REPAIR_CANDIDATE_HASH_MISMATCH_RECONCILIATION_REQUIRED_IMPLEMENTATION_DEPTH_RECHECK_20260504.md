# MVP4 Repair Candidate Hash Mismatch Reconciliation Required Implementation Depth Recheck

created_at_utc: 2026-05-04T13:39:03Z
patch_id: MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK_20260504_001

Finding:
- The repair candidate hash mismatch remains BLOCKED and live-affecting.
- The candidate rollup self-check is PASS, but the source expected rollup artifact remains MISSING.
- The operator queue keeps the item review-ready and hash-reconciliation-required.
- The candidate remains review-only with candidate_current_evidence_usable_count=0.

Patch:
- Added a depth report and contract_gap projection for REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED.
- Added regression tests for hash-mismatch depth, operator queue fail-closed behavior, and forward route.
- Kept REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED and BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION open, and advanced next_allowed_task_class to MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no scale-up
