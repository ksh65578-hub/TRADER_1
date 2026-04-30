# MVP4 Dashboard Actual Long-Run Floor UX Audit

created_at_utc: 2026-04-30T06:38:01Z
patch_id: MVP4_DASHBOARD_ACTUAL_LONG_RUN_FLOOR_UX_20260430_001

Finding:
- The dashboard could show operation history as validated after the configured display-history window while the Runtime Evidence Boundary also looked validated.
- That could make a clean one-hour display history appear equivalent to the stricter 86400s actual long-run PAPER/SHADOW evidence floor.

Patch:
- Runtime Evidence Boundary now remains ACTUAL_LONG_RUN_COLLECTING until observed stability history reaches at least 86400 seconds.
- Actual runtime duration, actual cycle count, evidence-window count, and recovery-clean checklist items stay COLLECTING below the floor.
- Operator text now explicitly explains that stable operation is not yet actual long-run evidence.
- UPBIT/BINANCE PAPER dashboard artifacts were regenerated through the safe launcher path.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
