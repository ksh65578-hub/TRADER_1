# MVP4 Upbit PAPER Post-Rerun Review Guidance Source Binding Guard Audit

created_at_utc: 2026-05-01T20:17:40Z
patch_id: MVP4_UPBIT_PAPER_POST_RERUN_REVIEW_GUIDANCE_SOURCE_BINDING_GUARD_20260502_001

Finding:
- The review guidance consumed the blocker rollup report object but did not independently prove the persisted blocker rollup artifact still matched that report.

Patch:
- Added source blocker rollup file load status, stored hash, recomputed hash, and hash-match fields to the review guidance report.
- The guidance now blocks missing, invalid, scope-mismatched, or hash-mismatched source blocker rollup files.
- Validator and runtime tests cover the missing-source negative case.

Runtime summary:
- review_guidance_status: BLOCKED_RECONCILIATION_REVIEW_REQUIRED
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
