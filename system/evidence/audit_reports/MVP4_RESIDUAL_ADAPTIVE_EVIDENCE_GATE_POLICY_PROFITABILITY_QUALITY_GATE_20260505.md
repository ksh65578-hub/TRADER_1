# MVP4 Profitability Adaptive Evidence Quality Gate

created_at_utc: 2026-05-05T14:27:51Z
patch_id: MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROFITABILITY_QUALITY_GATE_20260505_001

Patch:
- Removed the fixed PAPER runtime-hour floor from active profitability maturity evidence.
- Kept PAPER runtime hours as observed context only.
- Kept replay, OOS/walk-forward, PAPER trade count, SHADOW opportunity, net EV after cost, profit factor, drawdown, fill quality, paper/live parity, and open HIGH gap blockers visible.
- Updated the dashboard projection so operators see runtime as observed context rather than a duration pass/fail gate.

Safety:
- PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY remains OPEN.
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no live order
- no credential/API key use
- no LIVE_READY write
- no live config mutation
- no risk scale-up
