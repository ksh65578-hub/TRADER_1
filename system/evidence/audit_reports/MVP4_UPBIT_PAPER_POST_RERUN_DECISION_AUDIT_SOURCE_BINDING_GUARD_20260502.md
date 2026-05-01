# MVP4 Upbit PAPER Post-Rerun Decision Audit Source Binding Guard Audit

created_at_utc: 2026-05-01T19:59:57Z
patch_id: MVP4_UPBIT_PAPER_POST_RERUN_DECISION_AUDIT_SOURCE_BINDING_GUARD_20260502_001

Finding:
- The decision audit consumed the operator queue report object but did not independently prove the persisted operator queue artifact still matched that report.

Patch:
- Added source operator queue file load status, stored hash, recomputed hash, and hash-match fields to the decision audit report.
- The decision audit now blocks missing, invalid, scope-mismatched, or hash-mismatched source operator queue files.
- Validator and runtime tests cover the missing-source negative case.

Runtime summary:
- decision_audit_status: BLOCKED
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
