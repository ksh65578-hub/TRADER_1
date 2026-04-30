# MVP4 Upbit PAPER Candidate Decision Guard Audit

created_at_utc: 2026-04-30T14:06:44Z
patch_id: MVP4_UPBIT_PAPER_CANDIDATE_DECISION_GUARD_20260430_001

Finding:
- PAPER runtime candidate validation checked cost arithmetic and selected rank, but did not fully enforce that each candidate decision matched signal strength, net EV after cost, regime, and no-trade reason. A mutated or future candidate artifact could mark weak evidence as PAPER_ENTRY_REVIEW or silently suppress a threshold-passing candidate as NO_TRADE.

Patch:
- Added candidate decision threshold validation: PAPER_ENTRY_REVIEW requires net_ev_after_cost_bps > 5 and signal_strength >= 0.55.
- Added signal grade consistency validation.
- Added no-trade reason consistency validation.
- Tightened upbit_paper_runtime_cycle_report schema so candidate no_trade_reason references the registered no_trade_reason enum or null.
- Added negative tests for weak-signal entry review, signal grade mismatch, entry with no-trade reason, and threshold-passing candidate suppressed as NO_TRADE.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false

Remaining blocker:
- This improves PAPER evidence quality only. OOS/walk-forward evidence, official API verification, read-only burn-in, manual order evidence, operator approval, and live final guard remain required before any later live review.
