# READ_ONLY_DASHBOARD

context_pack_id: READ_ONLY_DASHBOARD
task_class: MVP4_DASHBOARD_LAUNCH_VISIBILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS", "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-ROOT-LAUNCHER-SURFACE"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.root_launcher_report.v1"]
included_validator_ids: ["read_only_dashboard_validator", "root_launcher_surface_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- root launchers generate session-scoped read-only dashboard HTML
- root launchers print dashboard_path
- interactive operator runs may open the local HTML dashboard
- dashboard remains display-only
- no order controls are present
- live_order_ready=false, live_order_allowed=false, can_live_trade=false

known_omissions_by_design:
- no standalone root dashboard launcher is added
- no web server is started
- no live order path is enabled
- no exchange credentials are loaded

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T21:49:42Z
