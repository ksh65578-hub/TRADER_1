# MVP4 Risk Exposure False-Safe Recheck Audit

created_at_utc: 2026-04-29T06:43:19Z
patch_id: MVP4_RISK_EXPOSURE_FALSE_SAFE_RECHECK_20260429_001

Finding:
- Missing or invalid PAPER drawdown was converted to 0.00%, allowing a false LOW_RISK dashboard state.
- Risk exposure schema allowed live and scale-up booleans as generic booleans even though runtime validation blocked them.
- Runtime validator used a broader data quality enum than the schema for drawdown status.

Patch:
- Missing drawdown now renders as ATTENTION/yellow with drawdown=UNVERIFIED.
- Dashboard now displays exposure and drawdown data quality separately.
- Risk exposure schema now requires display_only=true, dashboard_truth_only=true, live flags=false, scale_up_allowed=false, and scale_up blocker=SCALE_UP_NOT_ELIGIBLE.
- Added negative tests for missing drawdown hard truth, false low-risk drawdown, scale-up blocker drift, and schema/validator enum drift.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
