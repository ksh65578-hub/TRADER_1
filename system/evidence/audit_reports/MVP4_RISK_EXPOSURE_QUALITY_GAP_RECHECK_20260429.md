# MVP4 Risk Exposure Quality Gap Recheck

created_at_utc: 2026-04-29T08:17:27Z
patch_id: MVP4_RISK_EXPOSURE_QUALITY_GAP_RECHECK_20260429_001

Hidden defect:
- Risk Exposure could render LOW_RISK/green when exposure and drawdown values were zero even though paper_exposure_quality_report was not loaded.
- This did not enable live trading, but it could make a user believe risk evidence was complete.

Patch:
- Missing paper_exposure_quality_report now demotes Risk Exposure to ATTENTION/yellow.
- Added paper_exposure_quality_next_required_evidence to schema, runtime shell, HTML, and validator checks.
- Added negative tests for false LOW_RISK and missing next evidence.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
