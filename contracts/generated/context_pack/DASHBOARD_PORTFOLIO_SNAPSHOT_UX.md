# DASHBOARD_PORTFOLIO_SNAPSHOT_UX

context_pack_id: DASHBOARD_PORTFOLIO_SNAPSHOT_UX
task_class: MVP4_DASHBOARD_PORTFOLIO_SNAPSHOT_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD", "SECTION_MVP1_SUMMARY_SHELL"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-SUMMARY-SHELL", "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["read_only_dashboard_validator", "root_launcher_surface_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- first-screen dashboard exposes Cash, Equity, Open Positions, and Return as portfolio cards
- missing verified paper ledger or read-only account snapshot shows UNVERIFIED, not fabricated balances
- portfolio snapshot remains dashboard_serving_truth and display-only
- portfolio snapshot cannot create live_order_ready, live_order_allowed, can_live_trade, or scale_up_allowed
- dashboard HTML still has no order controls

known_omissions_by_design:
- no live account balance fetch is added
- no API key, secret, .env, or credential is used
- no real order, live config mutation, LIVE_READY snapshot, or LIVE_ENABLING_PATCH is introduced
- verified paper portfolio ledger ingestion remains a later safe task

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T22:24:36Z
