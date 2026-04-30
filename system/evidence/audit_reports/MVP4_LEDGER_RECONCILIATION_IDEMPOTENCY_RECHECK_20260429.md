# MVP4 Ledger Reconciliation Idempotency Recheck Audit

created_at_utc: 2026-04-29T06:53:31Z
patch_id: MVP4_LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK_20260429_001

Finding:
- Ledger chain validation blocked duplicate event_id and dedup_key, but could miss duplicate semantic events written with fresh ids.
- Intent WAL validation blocked duplicate WAL event ids, but could miss the same source ledger event written twice with fresh WAL ids.
- WAL/restart recovery schemas allowed live/order booleans as generic booleans while runtime validators blocked them.

Patch:
- Ledger chains now block duplicate event_type + intent_id + client_order_id + order_id combinations.
- Intent WAL chains now block duplicate source_ledger_event_hash values.
- WAL and restart recovery schemas now fix live/order permission fields to false and paper namespace separation to true.
- Added negative tests for duplicate semantic ledger events and duplicate source ledger WAL events.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
