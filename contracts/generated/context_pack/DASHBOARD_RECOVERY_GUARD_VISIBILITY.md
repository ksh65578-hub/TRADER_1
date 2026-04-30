# DASHBOARD_RECOVERY_GUARD_VISIBILITY

context_pack_id: DASHBOARD_RECOVERY_GUARD_VISIBILITY
task_class: MVP4_DASHBOARD_RECOVERY_GUARD_VISIBILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-RECOVERY-GUARD-VISIBILITY", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP4-UPBIT-PAPER-RUNTIME-RECOVERY-GUARD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_runtime_recovery_guard_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "upbit_paper_runtime_recovery_guard_validator", "root_launcher_surface_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "trader1/runtime/paper/upbit_paper_persistent_loop.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_recovery_guard_visibility_patch_evidence.py", "contracts/generated/context_pack/DASHBOARD_RECOVERY_GUARD_VISIBILITY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- dashboard first screen exposes PAPER runtime recovery separately from heartbeat freshness
- stale, missing, blocked, and invalid recovery guard states cannot look like normal RUNNING
- recovery guard PASS remains PAPER resume evidence only and cannot create live readiness
- generated dashboard_shell instances validate after schema expansion
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no private exchange call or credential load is performed
- recovery guard does not create long-run, promotion, scale-up, or LIVE_READY evidence
- browser screenshot QA remains a separate task because local Playwright is not installed in this environment

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-30T10:56:24Z
