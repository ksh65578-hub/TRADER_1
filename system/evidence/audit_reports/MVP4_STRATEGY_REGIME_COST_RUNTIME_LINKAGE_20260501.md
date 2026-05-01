# MVP4 Strategy Regime Cost Runtime Linkage Audit

created_at_utc: 2026-05-01T12:13:57Z
patch_id: MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE_20260501_001

Findings:
- Hidden issue: feature_snapshot and regime could be made internally plausible without being recomputed from the public market data payload.
- Hidden issue: candidate regime could diverge from the runtime regime while preserving candidate cost arithmetic.
- Hidden issue: candidate spread cost could diverge from feature spread while still presenting a valid expected_cost_bps sum.

Patch:
- Added strict runtime_public_market_data_hash, feature_snapshot_hash, and strategy_regime_cost_linkage fields.
- Added validator checks that recompute feature snapshot/regime from public market data and bind all candidates to runtime symbol/regime.
- Added validator checks that candidate spread cost matches feature spread.
- Added negative tests for feature/regime tamper, candidate regime mismatch, and spread-cost mismatch.
- Re-ran a bounded UPBIT/KRW_SPOT/PAPER runtime loop to refresh current runtime artifacts.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
