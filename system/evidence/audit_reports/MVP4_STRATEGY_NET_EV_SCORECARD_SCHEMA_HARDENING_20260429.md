# MVP4 Strategy Net EV Scorecard Schema Hardening

created_at_utc: 2026-04-29T00:45:18Z
patch_id: MVP4_STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING_20260429_001

Findings:
- candidate_scorecard previously allowed a minimal scaffold without cost-adjusted net EV fields.
- A raw positive edge could be operator-visible without fee, spread, slippage, market impact, latency, OOS, walk-forward, bootstrap, or overfit status.
- The scorecard could not create live permission, but it could weaken strategy and optimizer evidence quality.

Patch:
- Hardened candidate_scorecard schema with required NET_EV_AFTER_COST fields.
- Added candidate_scorecard_net_ev_validator.
- Added PASS and negative fixtures for raw-edge cost failure, live flag drift, and missing OOS evidence.
- Updated profitability evidence maturity audit while keeping the broader contract_gap open.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
