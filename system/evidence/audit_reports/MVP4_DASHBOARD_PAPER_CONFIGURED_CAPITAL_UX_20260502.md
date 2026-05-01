# MVP4 Dashboard PAPER Configured Capital UX Audit

created_at_utc: 2026-05-01T18:30:29Z
patch_id: MVP4_DASHBOARD_PAPER_CONFIGURED_CAPITAL_UX_20260502_001

Findings:
- Operators could see UNVERIFIED portfolio values and miss that UPBIT PAPER still has a configured 1,000,000 KRW starting-capital default.
- Showing that default as Cash or Equity would be unsafe because a stale or missing ledger cannot verify current portfolio truth.

Patch:
- summary.json now carries configured PAPER starting-capital metadata separately from cash, equity, PnL, and positions.
- the dashboard renders Configured PAPER Capital as a separate card.
- missing or stale ledger evidence still keeps Cash, Equity, PnL, and positions UNVERIFIED.
- validators block configured capital if it claims an exchange/live account source.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
