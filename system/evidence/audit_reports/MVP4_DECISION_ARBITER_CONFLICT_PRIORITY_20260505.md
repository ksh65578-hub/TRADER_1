# MVP4 Decision Arbiter Conflict Priority Audit

created_at_utc: 2026-05-05T14:55:44Z
patch_id: MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_DECISION_ARBITER_CONFLICT_PRIORITY_20260505_001

Finding:
- The PAPER decision arbiter selected unknown fallback blockers through set iteration, which could make primary_blocker_code nondeterministic when several blockers appeared together.
- The priority list also missed current registered blocker codes such as KILL_SWITCH_ACTIVE, LEDGER_INTEGRITY_FAIL, data freshness, cost, regime, and risk-scale blockers.

Patch:
- Added deterministic blocker normalization and ordering.
- Normalized legacy KILL_SWITCH to KILL_SWITCH_ACTIVE.
- Made reconciliation-family blockers force RECONCILE_REQUIRED in operational PAPER arbitration.
- Reused the same ordering for PAPER no_trade_reasons and primary_blocker_code in the paper broker and Upbit PAPER runtime.
- Added negative and ordering tests for kill/reconcile/live-guard/risk/data/cost/min-edge conflict cases.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false

Remaining blocker:
- This is traffic-control hardening only. Open external-evidence/operator-reconciliation gaps remain open and live readiness remains blocked.
