# MVP4_SHADOW_HARNESS_MEASUREMENT_SOURCE_GUARD

context_pack_id: MVP4_SHADOW_HARNESS_MEASUREMENT_SOURCE_GUARD
task_class: MVP4_SHADOW_HARNESS_MEASUREMENT_SOURCE_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SHADOW-HARNESS-MEASUREMENT-SOURCE-GUARD"]
included_schema_ids: ["trader1.shadow_observation_actual_runtime_harness_report.v1"]
included_validator_ids: ["shadow_observation_actual_runtime_harness_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/research/shadow/shadow_observation_actual_runtime_harness.py", "contracts/schema/shadow_observation_actual_runtime_harness_report.schema.json", "tests/research/test_shadow_observation_actual_runtime_harness.py", "trader1/validation/mvp0_validators.py", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py", "tools/emit_shadow_harness_measurement_source_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_SHADOW_HARNESS_MEASUREMENT_SOURCE_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- SHADOW actual runtime harness reports include a measurement source and monotonic timer verification flags.
- caller-supplied or unverified runtime measurement blocks operational harness PASS with MEASUREMENT_MISSING.
- false runtime_measurement_status drift is blocked by validator and tests.
- dashboard and launcher fixtures can only show short-window harness execution when measurement source is verified.
- long-run evidence, live readiness, live orders, and risk scale-up remain blocked.

known_omissions_by_design:
- this patch does not create real long-run PAPER/SHADOW evidence
- this patch does not use credentials or call exchange/account APIs
- this patch does not enable live orders, LIVE_READY snapshots, live config mutation, optimizer promotion, or risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T04:45:12Z
