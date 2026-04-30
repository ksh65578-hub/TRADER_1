# MVP4 Upbit Market Data Pointer Schema Guard

created_at_utc: 2026-04-30T16:48:54Z
patch_id: MVP4_UPBIT_MARKET_DATA_POINTER_SCHEMA_GUARD_20260501_001

Finding:
- Upbit public market-data latest pointer and collection writer artifacts were emitted but not independently schema/registry closed.

Patch:
- Added strict schemas and registry entries for latest pointer and collection writer report.
- Latest pointer now carries exchange, market_type, mode, session_id, symbol, report_hash, and public_market_data_hash.
- Collection writer report now carries symbol and public_market_data_hash in PASS/BLOCKED paths.
- Runtime schema instance validator covers generated collection, writer, and latest pointer instances.
- Added negative fixtures for pointer hash drift and writer live flag mutation.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential use
- no exchange private API call
- no live order path enabled
