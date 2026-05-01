# MVP4 Upbit PAPER Configured Portfolio Unverified Explanation Audit

created_at_utc: 2026-05-01T21:27:53Z
patch_id: MVP4_UPBIT_PAPER_CONFIGURED_PORTFOLIO_UNVERIFIED_EXPLANATION_20260502_001

Finding:
- Operators could see UNVERIFIED cash/equity and miss that 1,000,000 KRW is configured PAPER starting capital, not verified ledger cash.

Patch:
- Kept missing/stale ledger cash as UNVERIFIED.
- Added first-screen portfolio wording that explains configured PAPER capital versus verified simulated ledger cash/equity.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no current evidence writer or live config mutation added
