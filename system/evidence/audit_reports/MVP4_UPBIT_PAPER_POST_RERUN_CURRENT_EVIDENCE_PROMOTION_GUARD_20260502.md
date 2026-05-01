# MVP4 Upbit PAPER Post-Rerun Current Evidence Promotion Guard Audit

created_at_utc: 2026-05-01T15:40:48Z
patch_id: MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_20260502_001

Finding:
- Post-rerun candidate rollups were hash-linked and isolated, but there was no guard that made the promotion boundary explicit before any future current-evidence writer work.

Patch:
- Added a strict review-only promotion guard schema, runtime builder/writer/validator, registry entry, runtime artifact, patch-result fields, and negative tests.
- The guard verifies candidate rollup hashes, staged artifact scope, candidate role/status, and planned current-ledger path scope.
- Verified candidates are marked review-ready but remain blocked from current evidence writes.
- Current ledger JSONL, latest runtime pointer, persistent loop reports, source artifacts, live permission, promotion, long-run evidence, and scale-up remain blocked.

Runtime summary:
- promotion_guard_status: BLOCKED
- candidate_item_count: 8
- candidate_rollup_verified_count: 8
- promotion_review_ready_count: 8
- current_evidence_write_allowed_count: 0
- candidate_current_evidence_usable_count: 0

Safety:
- current_evidence_mutation_allowed=false
- current_evidence_write_allowed=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
