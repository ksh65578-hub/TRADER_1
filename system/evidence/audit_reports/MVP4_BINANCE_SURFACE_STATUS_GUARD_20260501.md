# MVP4 Binance Surface Status Guard

created_at_utc: 2026-04-30T16:07:08Z
patch_id: MVP4_BINANCE_SURFACE_STATUS_GUARD_20260501_001

Finding:
- Binance root launcher surface disclosed SPOT but needed explicit FUTURES_USDT_M blocked/not implemented wording to reduce operator confusion.

Patch:
- Added FUTURES_USDT_M blocked status constants to Binance root launchers.
- Root launcher guard now rejects Binance launcher files that disclose only SPOT or mention futures without blocked/not implemented status.
- Binance surface/dashboard wording now says FUTURES_USDT_M remains blocked and is not root-launchable in MVP-4.
- Added negative tests for SPOT-only Binance launcher disclosure and unsupported Binance market_type.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no Binance credential use
- no Binance public/private API call
- no live order path enabled
