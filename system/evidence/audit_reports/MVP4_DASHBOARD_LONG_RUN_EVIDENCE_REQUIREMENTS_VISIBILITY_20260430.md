# MVP4 Dashboard Long-Run Evidence Requirements Visibility Audit

created_at_utc: 2026-04-30T05:34:08Z
patch_id: MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY_20260430_001

Finding:
- Runtime Evidence Boundary told the operator actual long-run evidence was missing, but did not provide a fixed source/proof checklist.
- This could leave a user unsure whether persistent stubs, short-window harness output, or orchestration pairing were sufficient for live review.

Patch:
- Added an eight-item long-run evidence requirements checklist to the dashboard shell and HTML.
- Extended the dashboard schema so the checklist is mandatory and display-only.
- Extended dashboard validation to block missing/reordered checklist entries, live flag drift, hidden live-review blockers, and false PASS on actual long-run proof.
- Added positive and negative dashboard tests and regenerated safe local launcher dashboards.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
