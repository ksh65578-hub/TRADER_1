# MVP4 Upbit PAPER Post-Rerun Source Reconciliation Binding Guard Audit

created_at_utc: 2026-05-01T19:39:09Z
patch_id: MVP4_UPBIT_PAPER_POST_RERUN_SOURCE_RECONCILIATION_BINDING_GUARD_20260502_001

Finding:
- The current-evidence promotion guard consumed the source reconciliation report object but did not independently prove the persisted source artifact still matched that report.

Patch:
- Added source reconciliation file load status, stored hash, recomputed hash, and hash-match fields to the promotion guard report.
- The guard now blocks missing, invalid, or mismatched source reconciliation files.
- Validator and runtime tests cover the missing-source negative case.

Runtime summary:
- promotion_guard_status: BLOCKED
- source_file_load_status: PASS
- source_file_hash_match: True
- current_evidence_write_allowed_count: 0

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no current-evidence writer permission was added
