# DASHBOARD_PAPER_CONFIGURED_CAPITAL_UX

context_pack_id: DASHBOARD_PAPER_CONFIGURED_CAPITAL_UX
task_class: MVP4_DASHBOARD_PAPER_CONFIGURED_CAPITAL_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_SUMMARY_SHELL", "SECTION_MVP1_LEDGER", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-SUMMARY-SHELL", "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD", "REQ-MVP0-LIVE-BLOCKED-TEST"]
included_schema_ids: ["trader1.summary.v1", "trader1.read_only_dashboard_shell.v1", "trader1.paper_portfolio_snapshot.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "summary_shell_validator", "read_only_dashboard_validator", "paper_portfolio_snapshot_validator", "root_launcher_surface_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/summary_writer.py", "trader1/dashboard/read_only_dashboard.py", "contracts/schema/summary.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER default capital is visible as configured capital when the current portfolio source is UNVERIFIED
- configured capital is never displayed as verified cash, equity, PnL, or exchange balance
- summary validation blocks configured capital if it claims an exchange/live account source
- dashboard validation keeps live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no exchange balance is fetched
- no API key, secret, .env, or credential is used
- no live order, LIVE_READY snapshot, LIVE_ENABLING_PATCH, risk scale-up, or live config mutation is introduced
- stale or missing PAPER ledger evidence still keeps portfolio cash and equity UNVERIFIED

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-05-01T18:30:29Z
