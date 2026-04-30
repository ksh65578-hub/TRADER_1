# MVP4_LONG_RUN_EVIDENCE_THRESHOLD_FLOOR

context_pack_id: MVP4_LONG_RUN_EVIDENCE_THRESHOLD_FLOOR
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"]
included_requirement_ids: ["REQ-MVP4-LONG-RUN-EVIDENCE-THRESHOLD-FLOOR"]
included_schema_ids: ["trader1.shadow_observation_actual_runtime_blocker_report.v1", "trader1.shadow_observation_runtime_orchestration_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/research/shadow/shadow_observation_actual_runtime_blocker.py", "trader1/research/shadow/shadow_observation_runtime_orchestration.py", "contracts/schema/shadow_observation_actual_runtime_blocker_report.schema.json", "contracts/schema/shadow_observation_runtime_orchestration_report.schema.json", "tests/research/test_shadow_observation_actual_runtime_blocker.py", "tests/research/test_shadow_observation_runtime_orchestration.py", "tools/emit_long_run_threshold_floor_patch_evidence.py", "contracts/generated/context_pack/MVP4_LONG_RUN_EVIDENCE_THRESHOLD_FLOOR.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Actual long-run runtime blocker reports reject weakened runtime and cycle threshold floors.
- Runtime orchestration reports reject weakened runtime, cycle, and evidence-window threshold floors.
- Short-window PAPER/SHADOW harness output remains display/review evidence only, not long-run or live-ready evidence.
- Tests cover mutated low-threshold reports and preserve live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- no actual long-run runtime evidence is created by this patch
- no API keys, credentials, exchange account calls, order-capable endpoints, live orders, or scale-up are used
- ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING remains open

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T06:05:50Z
