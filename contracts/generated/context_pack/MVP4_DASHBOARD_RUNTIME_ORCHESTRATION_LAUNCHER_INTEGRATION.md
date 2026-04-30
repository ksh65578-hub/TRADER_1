# MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_LAUNCHER_INTEGRATION

context_pack_id: MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_LAUNCHER_INTEGRATION
task_class: MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_LAUNCHER_INTEGRATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-LAUNCHER-INTEGRATION"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.shadow_observation_runtime_orchestration_report.v1"]
included_validator_ids: ["read_only_dashboard_validator", "shadow_observation_runtime_orchestration_validator", "shadow_observation_actual_runtime_harness_validator", "shadow_observation_persistent_runtime_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/runtime/boot/safe_launcher.py", "tests/runtime/test_safe_launcher.py", "tools/emit_dashboard_runtime_orchestration_launcher_integration_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_LAUNCHER_INTEGRATION.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Safe launcher loads persistent runtime, short-window harness, and runtime orchestration artifacts from exact UPBIT/KRW_SPOT PAPER-to-SHADOW paths.
- Rendered dashboard shell lists runtime_orchestration_report.json only when the loaded status cites that source.
- Runtime orchestration remains display-only and blocks optimizer ranking, scorecard input, promotion, live orders, and scale-up.
- Actual UPBIT PAPER dashboard HTML can be regenerated without credentials and with all live flags false.

known_omissions_by_design:
- this patch does not create long-run PAPER/SHADOW runtime evidence
- this patch does not use API keys, credentials, exchange account calls, or live order APIs
- this patch does not enable LIVE_READY, live orders, live config mutation, optimizer promotion, or scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T05:22:37Z
