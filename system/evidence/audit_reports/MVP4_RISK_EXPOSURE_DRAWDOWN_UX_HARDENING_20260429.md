# MVP4 Risk Exposure Drawdown UX Hardening Audit

created_at_utc: 2026-04-29T02:23:43Z
patch_id: MVP4_RISK_EXPOSURE_DRAWDOWN_UX_HARDENING_20260429_001

Finding:
- Dashboard first-screen status showed portfolio values and blockers, but did not summarize PAPER exposure, drawdown, or scale-up blocked state in a way an operator could scan quickly.
- A false-safe UX path existed: missing position notional could be visually buried in the position table instead of triggering a yellow risk review state.

Patch:
- Added a display-only Risk Exposure panel to the read-only dashboard.
- Added schema and validator checks so LOW_RISK requires fresh verified PAPER portfolio values and cannot hide exposure or drawdown.
- Added negative tests for scale-up drift, false low-risk display without verified portfolio, stale summary demotion, and missing position notional warning.
- Refreshed UPBIT and BINANCE PAPER runtime dashboard artifacts.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
