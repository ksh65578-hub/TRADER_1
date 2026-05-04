# MVP4 Profitability Optimizer Evidence Maturity Recheck

created_at_utc: 2026-05-04T05:15:25Z
patch_id: MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK_20260504_001

Patch:
- Added schema-backed promotion_threshold_evidence to the profitability maturity rollup.
- Validator now fails closed if threshold evidence claims PASS while replay, OOS/walk-forward, PAPER, SHADOW, parity, quality, or HIGH contract-gap evidence is insufficient.
- Contract gap remains OPEN and live-affecting.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
