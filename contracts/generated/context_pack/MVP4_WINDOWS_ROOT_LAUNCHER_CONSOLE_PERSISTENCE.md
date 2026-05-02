# MVP4_WINDOWS_ROOT_LAUNCHER_CONSOLE_PERSISTENCE

context_pack_id: MVP4_WINDOWS_ROOT_LAUNCHER_CONSOLE_PERSISTENCE
task_class: MVP4_WINDOWS_ROOT_LAUNCHER_CONSOLE_PERSISTENCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_ROOT_LAUNCHER_SCOPE", "SECTION_MVP1_HEARTBEAT", "SECTION_MVP1_SAFE_BOOT_SEQUENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP1-HEARTBEAT", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP0-LIVE-BLOCKED-TEST"]
included_schema_ids: ["trader1.root_launcher_report.v1", "trader1.heartbeat.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["root_launcher_guard_validator", "root_launcher_surface_validator", "heartbeat_validator", "read_only_dashboard_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator"]
included_artifact_ids: ["BINANCE_LIVE.py", "BINANCE_PAPER.py", "UPBIT_LIVE.py", "UPBIT_PAPER.py", "contracts/generated/context_pack/MVP4_WINDOWS_ROOT_LAUNCHER_CONSOLE_PERSISTENCE.md", "tests/contract/test_root_launchers.py", "tests/runtime/test_safe_launcher.py", "tools/emit_windows_console_safe_monitor_default_patch_evidence.py", "tools/emit_windows_root_launcher_console_persistence_patch_evidence.py", "trader1/runtime/boot/safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- root launchers enter operator SAFE_MONITOR by default so a Windows console does not close after one heartbeat
- automation can bound root launcher execution with TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS and TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS
- root launcher guard still exposes exactly four allowed launchers
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- this is not a persistent trading engine
- this does not create PAPER portfolio verification, LIVE_READY, live order permission, credentials, or scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-05-02T00:12:33Z
