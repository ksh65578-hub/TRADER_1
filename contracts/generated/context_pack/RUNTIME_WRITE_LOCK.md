# RUNTIME_WRITE_LOCK

context_pack_id: RUNTIME_WRITE_LOCK
task_class: MVP4_RUNTIME_WRITE_LOCK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_ROOT_LAUNCHER_SCOPE", "SECTION_DASHBOARD_SHELL", "SECTION_MVP2_RESTART_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP2-RESTART-RECOVERY-SKELETON"]
included_schema_ids: ["trader1.root_launcher_report.v1", "trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["root_launcher_surface_validator", "read_only_dashboard_validator", "summary_shell_validator", "live_blocked_scaffold_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/boot/safe_launcher.py", "tests/runtime/test_safe_launcher.py", "tools/emit_dashboard_launch_visibility_patch_evidence.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- runtime launcher report, summary, heartbeat, paper portfolio, dashboard shell, and dashboard HTML are written under a session-scoped writer lock
- same-session concurrent writers fail closed instead of producing mixed artifact sets
- launcher_main uses a single bundle write for report and dashboard artifacts
- temporary writes use replace semantics and clean local temp files after exceptions
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order path is enabled
- no API key, secret, .env, or credential is used
- no optimizer/convergence output can create live permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T22:52:59Z
