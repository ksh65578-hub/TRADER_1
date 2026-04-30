# MVP4 Dashboard Stale Rollup Truth Guard Audit

created_at_utc: 2026-04-30T13:58:44Z
patch_id: MVP4_DASHBOARD_STALE_ROLLUP_TRUTH_GUARD_20260430_001

Finding:
- A stale PAPER ledger rollup could be loaded from the scoped dashboard path. Without an explicit freshness gate at portfolio binding time, the dashboard could treat stale ledger-derived portfolio data as verified display truth.

Patch:
- Dashboard portfolio binding now uses PAPER ledger rollup only when rollup_status=PASS and the rollup is fresh.
- If a stale rollup exists and no fresh runtime cycle exists, the dashboard portfolio remains UNVERIFIED instead of falling back to a fresh-looking initial scaffold.
- Added runtime negative tests for stale rollup with and without a fresh runtime cycle.
- Extended read_only_dashboard_validator to reproduce stale rollup plus missing latest runtime cycle and require UNVERIFIED display.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false

Remaining blocker:
- Live readiness still requires external official API verification, read-only burn-in, manual order evidence, operator approval, and live final guard PASS for exact scope.
