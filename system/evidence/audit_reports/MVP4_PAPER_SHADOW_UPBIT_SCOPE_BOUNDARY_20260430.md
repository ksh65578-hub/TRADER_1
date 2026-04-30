# MVP4 Paper Shadow Upbit Scope Boundary Audit

created_at_utc: 2026-04-30T06:29:27Z
patch_id: MVP4_PAPER_SHADOW_UPBIT_SCOPE_BOUNDARY_20260430_001

Finding:
- MVP-4 paper/shadow evidence accumulation could accept BINANCE/SPOT as a supported scorecard input scope.
- Binance scaffolds can exist for later-stage paper/dashboard work, but they must not be treated as MVP-4 Upbit live-review evidence.

Patch:
- Restricted paper/shadow evidence accumulation scope to UPBIT/KRW_SPOT.
- Restricted paper/shadow evidence schema exchange, market_type, and artifact path patterns to upbit/krw_spot paper and shadow namespaces.
- Added a negative test proving BINANCE/SPOT cannot become MVP-4 paper scorecard input.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
