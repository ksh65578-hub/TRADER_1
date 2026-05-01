# MVP4 Upbit PAPER Post-Rerun Blocker Rollup Source Binding Guard Audit

created_at_utc: 2026-05-01T20:09:44Z
patch_id: MVP4_UPBIT_PAPER_POST_RERUN_BLOCKER_ROLLUP_SOURCE_BINDING_GUARD_20260502_001

Finding:
- The blocker rollup consumed the decision audit report object but did not independently prove the persisted decision audit artifact still matched that report.

Patch:
- Added source decision audit file load status, stored hash, recomputed hash, and hash-match fields to the blocker rollup report.
- The blocker rollup now blocks missing, invalid, scope-mismatched, or hash-mismatched source decision audit files.
- Validator and runtime tests cover the missing-source negative case.

Runtime summary:
- blocker_rollup_status: BLOCKED
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
