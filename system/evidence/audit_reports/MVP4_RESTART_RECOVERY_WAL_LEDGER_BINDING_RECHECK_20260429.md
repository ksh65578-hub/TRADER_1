# MVP4 Restart Recovery WAL Ledger Binding Recheck

created_at_utc: 2026-04-29T08:23:26Z
patch_id: MVP4_RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK_20260429_001

Hidden defect:
- Restart recovery validated ledger chain and intent WAL chain independently.
- A WAL event could point to a ledger hash outside the recovered ledger chain if the WAL hash chain was recomputed.
- A recovered idempotent ledger event could be missing from WAL while both chains still looked individually valid.

Patch:
- WAL source_ledger_event_hash now requires sha256 hex shape.
- Restart recovery requires WAL source hashes to be contained in recovered ledger event hashes.
- Restart recovery requires every recovered ledger event with intent/client ids to have a WAL source entry.
- Added negative tests for outside-ledger WAL source, missing WAL source, and non-hex source hash.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
