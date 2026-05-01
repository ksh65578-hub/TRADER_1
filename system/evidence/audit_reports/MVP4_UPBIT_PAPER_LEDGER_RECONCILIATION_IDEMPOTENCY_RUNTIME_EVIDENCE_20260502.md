# MVP4 Upbit PAPER Ledger Idempotency Runtime Evidence Audit

created_at_utc: 2026-05-01T21:57:22Z
patch_id: MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RUNTIME_EVIDENCE_20260502_001

Patch:
- Added a current-runtime Upbit PAPER ledger idempotency evidence producer.
- The producer rereads the canonical PAPER ledger rollup and recomputes event counts, fill counts, duplicate event ids, duplicate dedup keys, duplicate semantic events, duplicate filled order keys, and portfolio provenance.
- Added a closed schema, validator, and negative fixtures for duplicate ledger events, live permission mutation, path escape, and count mismatch.

Runtime evidence:
- runtime_evidence_status=PASS
- idempotency_status=PASS
- reconciliation_status=PASS
- portfolio_provenance_status=PASS
- source_ledger_jsonl_count=28
- recomputed_ledger_event_count=168
- duplicate_event_id_count=0

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- post-rerun and long-run blockers remain open
