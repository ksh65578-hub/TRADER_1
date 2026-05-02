# MVP4 Upbit PAPER Runtime Evidence Collection Profile

created_at_utc: 2026-05-02T03:28:53Z
patch_id: MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE_20260502_001

Patch:
- Added a bounded Upbit PAPER runtime evidence collection profile.
- The profile validates persistent loop, recovery guard, runtime sample history, and ledger idempotency evidence together.
- Duplicate ledger evidence is tested as RECONCILIATION_REQUIRED.

Audit:
- profile_status: PASS
- component_pass_count: 4/4
- accepted_cycle_sample_count: 2
- ledger_runtime_evidence_status: PASS
- mismatch_count: 0

Safety:
- long_run_evidence_eligible=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
