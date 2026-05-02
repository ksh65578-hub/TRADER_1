# MVP4 Upbit PAPER Ledger Idempotency Runtime Evidence Refresh

created_at_utc: 2026-05-02T04:20:03Z
patch_id: MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_REFRESH_20260502_001

Patch:
- Added a safe refresh command for current Upbit PAPER ledger idempotency runtime evidence.
- The command writes scoped PAPER evidence only and rejects escaped, live, or non-json output paths.
- The launcher dashboard now sees the refreshed idempotency/reconciliation status as current display truth.
- Duplicate-ledger fixtures remain blocked as RECONCILIATION_REQUIRED.

Runtime evidence:
- runtime_evidence_status=PASS
- idempotency_status=PASS
- reconciliation_status=PASS
- portfolio_provenance_status=PASS
- source_ledger_jsonl_count=28
- recomputed_ledger_event_count=168
- mismatch_count=0

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials, private account calls, live orders, live config mutation, or risk scale-up
