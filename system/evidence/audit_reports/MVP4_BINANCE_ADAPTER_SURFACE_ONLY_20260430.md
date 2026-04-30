# MVP4 Binance Adapter Surface-Only Boundary Audit

created_at_utc: 2026-04-30T13:40:29Z
patch_id: MVP4_BINANCE_ADAPTER_SURFACE_ONLY_20260430_001

Finding:
- Binance root launchers and dashboard artifacts existed, but the repo had no explicit Binance adapter namespace. That could make visible Binance launchers look more implemented than they are.

Patch:
- Added trader1.adapters.binance as a fail-closed SURFACE_ONLY namespace.
- Added strict binance_adapter_surface_report schema and validator.
- Added BINANCE_ADAPTER_SURFACE_ONLY and BINANCE_FUTURES_SURFACE_ONLY blocker codes to registry/common defs.
- Root launcher and dashboard artifacts now expose Binance-specific surface-only blockers.
- Negative tests block credential loading, order adapter calls, live flag drift, futures readiness claims, and scale-up drift.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false

Remaining blocker:
- Binance SPOT/FUTURES paper runtime and any live behavior remain unimplemented and blocked until later staged evidence exists.
