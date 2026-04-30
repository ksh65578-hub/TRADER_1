# OPTIMIZER_MEMORY_STATE_SCHEMA

context_pack_id: OPTIMIZER_MEMORY_STATE_SCHEMA
task_class: MVP4_OPTIMIZER_MEMORY_STATE_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_OPTIMIZER_MEMORY", "SECTION_CONVERGENCE_MEMORY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-OPTIMIZER-MEMORY-STATE-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.optimizer_memory_state.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "optimizer_memory_state_validator", "optimization_state_validator", "optimizer_guardrail_report_validator", "optimizer_run_report_validator", "optimizer_recommendation_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/optimizer_memory_state.schema.json", "contracts/registry.yaml", "contracts/validators/fixture_catalog.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_optimizer_memory_state_validator.py", "tests/validators/fixtures/optimizer_memory_state_pass.json", "tests/validators/fixtures/optimizer_memory_state_live_flag_fail.json", "tests/validators/fixtures/optimizer_memory_state_reset_without_audit_fail.json", "tests/validators/fixtures/optimizer_memory_state_forget_failed_candidate_fail.json", "tests/validators/fixtures/optimizer_memory_state_cross_scope_reuse_fail.json", "tests/validators/fixtures/optimizer_memory_state_failed_candidate_unblocked_fail.json", "tests/validators/fixtures/optimizer_memory_state_append_without_hash_fail.json", "tests/validators/fixtures/optimizer_memory_state_live_source_mode_fail.json", "tools/run_optimizer_memory_state_validators.py", "tools/emit_optimizer_memory_state_schema_hardening_patch_evidence.py", "contracts/generated/context_pack/OPTIMIZER_MEMORY_STATE_SCHEMA.md", "system/evidence/audit_reports/MVP4_OPTIMIZER_MEMORY_STATE_SCHEMA_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- optimizer memory is append-audit-only and hash-linked
- failed, blocked, and retired candidates remain retained
- memory reset without audit is impossible
- failed candidates cannot become promotion or live-order eligible
- cross-scope memory reuse remains forbidden
- memory cannot create live readiness, live orders, exchange account calls, ACTIVE snapshot mutation, live config mutation, or scale-up permission
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- optimizer memory is not execution truth and is not dashboard truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T04:30:25Z
