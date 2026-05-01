# MVP4 Upbit PAPER Post-Rerun Review Guidance Dashboard Binding Audit

created_at_utc: 2026-05-01T17:46:22Z
patch_id: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_DASHBOARD_BINDING_20260502_001

Finding:
- Post-rerun operator review guidance existed as a review-only runtime artifact, but the launcher dashboard did not yet expose its counts and blocker state directly.

Patch:
- Bound the review guidance report into the read-only dashboard and launcher source map.
- Surfaced guidance status, item count, review step count, forbidden output count, and zero current-evidence write count in the reconciliation panel.
- Kept POST_RERUN_RECONCILIATION_REQUIRED as the dashboard blocking reason and operator primary blocker.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no current evidence writer or live config mutation added
