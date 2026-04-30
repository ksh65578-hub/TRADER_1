# STALE_HEARTBEAT_RECOVERY_GUIDANCE

context_pack_id: STALE_HEARTBEAT_RECOVERY_GUIDANCE
task_class: MVP4_STALE_HEARTBEAT_RECOVERY_GUIDANCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-STALE-HEARTBEAT-RECOVERY-GUIDANCE", "REQ-MVP1-HEARTBEAT", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "heartbeat_validator", "read_only_dashboard_validator", "root_launcher_surface_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/boot/safe_launcher.py", "trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/runtime/test_safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tools/run_stale_heartbeat_recovery_guidance_validators.py", "tools/emit_stale_heartbeat_recovery_guidance_patch_evidence.py", "contracts/generated/context_pack/STALE_HEARTBEAT_RECOVERY_GUIDANCE.md"]

acceptance_checklist:
- stale heartbeat cannot be displayed as RUNNING_SAFE_MODE in console heartbeat output
- dashboard operation status includes recovery guidance
- read_only_dashboard_shell schema metric count matches emitted stability metrics
- normal is green/blue, warning is yellow, error is red
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false

known_omissions_by_design:
- no live order path is enabled
- no credential, exchange account call, or live burn-in is performed
- dashboard guidance is display truth only and cannot create execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T23:59:13Z
