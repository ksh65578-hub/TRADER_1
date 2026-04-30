# ACTIVE_WORKING_VIEW

generated_at_utc: 2026-04-30T16:30:07Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD_20260501_001
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Upbit PAPER collection-backed runtime now binds the exact public market data payload hash from collection to runtime cycle. A cycle with mutated public_market_data after collection binding fails closed as SCHEMA_IDENTITY_MISMATCH.

## Next Safe Task

MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE
