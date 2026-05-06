# MVP4 PAPER Risk Exposure Truth Binding Audit

created_at_utc: 2026-05-06T07:09:12Z
patch_id: MVP4_PAPER_CURRENT_TRUTH_REFRESH_WRITER_RISK_EXPOSURE_TRUTH_BINDING_20260506_001

Patch:
- Risk exposure keeps last verified stale PAPER ledger values as STALE display truth.
- Drawdown uses equity_high=max(configured_starting_cash,current_equity).
- Position notional prefers ledger market_value when available.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials
- no live order path
- no LIVE_READY write
- no live config mutation
- no risk scale-up
