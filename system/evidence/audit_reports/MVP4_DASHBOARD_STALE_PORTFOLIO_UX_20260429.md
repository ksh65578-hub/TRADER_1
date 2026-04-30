# MVP4 Dashboard Stale Portfolio UX Audit

created_at_utc: 2026-04-28T22:47:18Z
patch_id: MVP4_DASHBOARD_STALE_PORTFOLIO_UX_20260429_001

Findings:
- A stale summary artifact could still serve PAPER portfolio values as if they were current display truth.
- A future-dated summary from clock skew could also be interpreted as fresh.
- The visible status word VERIFIED could be misread as exchange or live account verification.
- current_implementation_state listed live_blocked_scaffold_validator as implemented, but the runtime validator table did not expose a callable function for full-registry execution.

Patch:
- Dashboard source freshness now uses generated_at_utc with an age and future-skew guard.
- Stale or future-dated summary artifacts demote portfolio values to STALE/UNVERIFIED.
- Fresh PAPER portfolio display now renders as PAPER LEDGER VERIFIED (SIMULATED).
- Added stale and future-skew negative tests.
- Added live_blocked_scaffold_validator runtime wiring and a test that every implemented validator in current_implementation_state is callable.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
