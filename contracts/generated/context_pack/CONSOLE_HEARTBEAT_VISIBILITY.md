# CONSOLE_HEARTBEAT_VISIBILITY

context_pack_id: CONSOLE_HEARTBEAT_VISIBILITY
task_class: MVP4_CONSOLE_HEARTBEAT_VISIBILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_ROOT_LAUNCHER_SCOPE", "SECTION_MVP1_HEARTBEAT", "SECTION_MVP1_SAFE_BOOT_SEQUENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP1-HEARTBEAT", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"]
included_schema_ids: ["trader1.root_launcher_report.v1", "trader1.heartbeat.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["root_launcher_guard_validator", "root_launcher_surface_validator", "heartbeat_validator", "read_only_dashboard_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/boot/safe_launcher.py", "tests/runtime/test_safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- root launchers print bounded console heartbeat lines
- console heartbeat states RUNNING_SAFE_MODE, not live ready
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false
- no order adapter submit is attempted

known_omissions_by_design:
- no long-running trading loop is introduced
- no live key loading
- no live order API
- no MVP-5 live-enabling behavior

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T22:04:40Z
