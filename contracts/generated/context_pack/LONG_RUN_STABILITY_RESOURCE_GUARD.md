# LONG_RUN_STABILITY_RESOURCE_GUARD

context_pack_id: LONG_RUN_STABILITY_RESOURCE_GUARD
task_class: MVP4_LONG_RUN_STABILITY_RESOURCE_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-LONG-RUN-STABILITY-RESOURCE-GUARD", "REQ-MVP1-HEARTBEAT", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"]
included_schema_ids: ["trader1.heartbeat.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "heartbeat_validator", "read_only_dashboard_validator", "runtime_stability_history_validator", "runtime_resource_pressure_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/health/runtime_resource_pressure.py", "trader1/runtime/boot/safe_launcher.py", "trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "contracts/schema/read_only_dashboard_shell.schema.json", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tests/runtime/test_runtime_resource_pressure.py", "tests/runtime/test_safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tools/run_runtime_resource_pressure_validators.py", "tools/emit_runtime_resource_pressure_guard_patch_evidence.py", "contracts/generated/context_pack/LONG_RUN_STABILITY_RESOURCE_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- runtime artifact count, disk bytes, temp write files, and stale write lock are inspected
- stale write lock or hard artifact pressure becomes RESOURCE_LIMIT_BLOCK
- dashboard shows Runtime artifact pressure as its own stability metric
- warning state uses yellow; failure state uses red; normal state remains green or blue
- no live readiness, live order permission, trading permission, or scale-up permission is created

known_omissions_by_design:
- no live order path is enabled
- no exchange account call, credential load, or live burn-in is performed
- resource pressure is a safety/UX guard, not trading alpha or LIVE_READY evidence

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T23:49:53Z
