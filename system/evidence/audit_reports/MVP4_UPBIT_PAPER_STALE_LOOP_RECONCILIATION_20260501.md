# MVP4 Upbit PAPER Stale Loop Reconciliation Audit

created_at_utc: 2026-05-01T00:24:15Z
patch_id: MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_20260501_001

Finding:
- Runtime sample history showed stale persistent loop reports, but the operator could not see which reports were current evidence and which were legacy/schema-drift references.
- Without an explicit reconciliation report, stale reports could be misread as long-run PAPER evidence or silently inflate history.

Patch:
- Added strict stale loop reconciliation schema, runtime builder/writer/validator, runtime artifact, registry entry, and negative tests.
- The report classifies current-schema PASS, legacy schema drift, corrupt JSON, unsafe live/order flag mutations, and duplicate runtime cycle hashes.
- The report performs no deletion and allows only current-schema PASS loop reports as current evidence.

Runtime reconciliation summary:
- reconciliation_status: BLOCKED
- source_loop_report_count: 17
- current_accepted_count: 1
- legacy_schema_drift_count: 16
- unsafe_blocked_count: 0
- invalid_json_count: 0
- duplicate_runtime_cycle_hash_count: 0
- current_evidence_usable_count: 1

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no stale runtime artifact deletion performed
