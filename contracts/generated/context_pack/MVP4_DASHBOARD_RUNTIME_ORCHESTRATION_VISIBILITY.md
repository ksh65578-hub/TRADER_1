# MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_VISIBILITY

context_pack_id: MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_VISIBILITY
task_class: MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_VISIBILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-VISIBILITY"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["read_only_dashboard_validator", "shadow_observation_runtime_orchestration_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_runtime_orchestration_visibility_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_VISIBILITY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard exposes Runtime Orchestration Guard as display truth only.
- Source pairing, source validation, observed runtime count, optimizer ranking block, scorecard block, and live block are visible.
- Runtime orchestration source artifact must be listed when loaded.
- Runtime orchestration live, scorecard, promotion, order, scale, or long-run runtime drift blocks validation.
- All live flags remain false.

known_omissions_by_design:
- this patch does not create durable long-run PAPER/SHADOW runtime evidence
- this patch does not use credentials or call exchange/account APIs
- this patch does not enable live orders, LIVE_READY snapshots, live config mutation, optimizer promotion, or risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T05:12:36Z
