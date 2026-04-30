# MVP4 Dashboard Visual Layout QA Audit

created_at_utc: 2026-04-30T11:16:53Z
patch_id: MVP4_DASHBOARD_VISUAL_LAYOUT_QA_20260430_001

Findings:
- Hidden issue: runtime dashboard HTML can become stale even when dashboard_shell.json and Python rendering code have advanced.
- Hidden issue: detail drawer persistence used DOM index plus label, so adding or reordering drawers could reset or misapply operator-expanded state.
- UX risk: fixed 3-column first-screen and fixed KPI/ledger grids can make long tokens such as BOOTSTRAP_READ_ONLY feel cramped.

Patch:
- First screen now uses a wider two-column grid with portfolio spanning two rows.
- Portfolio KPI, ledger, quicklook, and operation status grids now use overflow-safe minmax constraints.
- Detail drawers now carry stable data-detail-key values.
- Added dashboard_visual_layout_validator and refresh_runtime_dashboard_html tooling.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
