# MVP4 Upbit PAPER Runtime Source Hash Guard

created_at_utc: 2026-04-30T16:30:07Z
patch_id: MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD_20260501_001

Finding:
- A collection-backed Upbit PAPER runtime cycle bound only the collection report hash and canonical event count. If public_market_data was changed after binding, the cycle could still be rehashed internally and pass without proving it matched the original collection payload.

Patch:
- Added public_market_data_hash to Upbit public collection reports and schema.
- Added source_public_market_data_hash to Upbit PAPER runtime cycle reports and schema.
- Runtime validation recomputes public_market_data_hash and fails closed on source payload mismatch.
- Latest collection pointer and writer report expose public_market_data_hash for traceability.
- Added unit/integration and validator negative fixtures for payload mutation.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential use
- no exchange private API call
- no live order path enabled
