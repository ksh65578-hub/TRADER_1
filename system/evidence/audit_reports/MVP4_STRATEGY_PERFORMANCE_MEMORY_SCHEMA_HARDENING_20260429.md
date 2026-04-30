# MVP4 Strategy Performance Memory Schema Hardening Audit

created_at_utc: 2026-04-29T04:42:54Z
patch_id: MVP4_STRATEGY_PERFORMANCE_MEMORY_SCHEMA_HARDENING_20260429_001

Findings:
- strategy_performance_memory was scaffold-level and could not distinguish raw PnL from net EV after costs.
- Strategy performance memory did not require entry, exit, and no-trade reasons, making operator UX and missed-entry analysis opaque.
- Regime-specific performance was not required, so downtrend/risk-off behavior could be invisible to optimizer and convergence logic.
- Paper/shadow evidence separation was not enforced in this memory artifact.

Patch:
- Hardened strategy_performance_memory schema with net EV after fee/spread/slippage/impact, regime rows, reason counts, sample thresholds, paper/shadow separation, and false live/scale/exchange flags.
- Added strategy_performance_memory_validator and made optimizer_guardrail_validator depend on it.
- Added PASS and negative fixtures for live flag drift, raw PnL masking negative net EV, insufficient samples, missing reasons, downtrend trading, live source mixing, and unscoped source mixing.
- Added unit tests and standalone validator runner.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
