# MVP4 Upbit PAPER Stale Loop Post-Regeneration Reconciliation Audit

created_at_utc: 2026-05-01T01:51:30Z
patch_id: MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_RECONCILIATION_20260501_001

Finding:
- Safe regeneration created current-schema replacement artifacts, but there was no post-regeneration report separating usable PASS replacements from schema-repaired replacements that still require ledger/recovery reconciliation.
- The generic stale-loop reconciliation saw source/replacement lineage hash overlap as duplicate runtime hashes, which is correct before regeneration but too coarse after source-retaining repair.

Patch:
- Added post-regeneration reconciliation schema, runtime builder/writer/validator, registry entry, runtime artifact, and negative tests.
- PASS regenerated replacements are usable as current PAPER evidence.
- RECONCILIATION_REQUIRED regenerated replacements remain excluded from current evidence.
- Source artifacts remain retained and excluded; no delete or overwrite is allowed.

Runtime summary:
- post_reconciliation_status: BLOCKED
- planned_regeneration_item_count: 16
- regenerated_current_accepted_count: 10
- regenerated_current_blocked_reconciliation_count: 6
- current_evidence_usable_count: 10
- excluded_from_current_evidence_count: 6

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
