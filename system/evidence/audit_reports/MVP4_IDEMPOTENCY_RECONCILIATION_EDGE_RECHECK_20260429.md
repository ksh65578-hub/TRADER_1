# MVP4 Idempotency Reconciliation Edge Recheck

created_at_utc: 2026-04-29T09:07:17Z
patch_id: MVP4_IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK_20260429_001

Findings:
- Ambiguous idempotency states were only forced into reconciliation when a new identifier was proposed or the identifier changed.
- Same-identifier ambiguous transport states could be reported with a later live-enabling blocker instead of RECONCILIATION_REQUIRED.
- Missing original identifiers in ambiguous states could hide the need for reconciliation before submit.

Patch:
- Any PENDING_CONFIRM, RECONCILE_REQUIRED, or TRANSPORT_AMBIGUOUS state now adds RECONCILIATION_REQUIRED before live gate fallback.
- Added negative tests for same-identifier and missing-original-identifier ambiguous states.
- Strengthened single_writer_order_path_validator to cover both edge cases.

Audit:
- same_identifier_primary_blocker: RECONCILIATION_REQUIRED
- same_identifier_final_decision: RECONCILE_REQUIRED
- missing_original_primary_blocker: RECONCILIATION_REQUIRED
- missing_original_final_decision: RECONCILE_REQUIRED

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
