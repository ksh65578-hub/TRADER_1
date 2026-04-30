# MVP4 Upbit PAPER Runtime Candidate Linkage Cost Model Audit

created_at_utc: 2026-04-30T11:31:51Z
patch_id: MVP4_UPBIT_PAPER_RUNTIME_CANDIDATE_LINKAGE_COST_MODEL_20260430_001

Findings:
- Hidden issue: selected_candidate could diverge from strategy_candidates while still presenting a plausible PAPER cycle.
- Hidden issue: sizing_decision.strategy_unit_id was not explicitly tied back to selected_candidate.candidate_id.
- Hidden issue: net EV after cost existed as a number, but the PAPER runtime candidate did not expose fee, slippage, spread, impact, and latency components as validator-checkable evidence.

Patch:
- Added strict PAPER runtime candidate schema fields for cost breakdown and live-blocked candidate flags.
- Added validator checks for selected-candidate membership, highest net EV after cost, candidate cost arithmetic, risk-off no-trade, and sizing linkage.
- Added negative tests for wrong selected candidate, sizing mismatch, missing cost breakdown, and cost component mismatch.
- Re-ran a bounded UPBIT/KRW_SPOT/PAPER runtime loop to refresh current runtime artifacts.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
