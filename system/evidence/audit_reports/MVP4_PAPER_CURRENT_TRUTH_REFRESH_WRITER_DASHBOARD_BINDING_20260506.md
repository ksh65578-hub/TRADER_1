# MVP4 PAPER Current Truth Refresh Dashboard Binding Audit

created_at_utc: 2026-05-06T07:39:59Z
patch_id: MVP4_PAPER_CURRENT_TRUTH_REFRESH_WRITER_DASHBOARD_BINDING_20260506_001

Patch:
- Dashboard portfolio truth can consume paper_current_truth_refresh_report.json when it is fresh and scoped.
- Stale refresh remains stale display-only truth.
- Refresh live/scale permission drift becomes BLOCKED display truth.

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
