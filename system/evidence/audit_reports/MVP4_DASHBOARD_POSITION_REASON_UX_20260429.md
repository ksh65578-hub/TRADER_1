# MVP4 Dashboard Position Reason UX Audit

created_at_utc: 2026-04-28T23:09:25Z
patch_id: MVP4_DASHBOARD_POSITION_REASON_UX_20260429_001

Findings:
- Dashboard showed portfolio counts but did not show a direct trading decision trace.
- No-trade reason, entry status, exit status, and open PAPER position detail were not visible enough for an operator.
- Position and decision display needed explicit guardrails so UI truth could not become execution truth.

Patch:
- Added decision_trace to dashboard shell and schema.
- Added position_snapshot to dashboard shell and schema.
- Rendered Trading Decision and Open PAPER Positions sections on the dashboard first screen.
- Added negative tests for decision live permission drift, no-trade reason mismatch, position execution-truth claim, and position live permission drift.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
