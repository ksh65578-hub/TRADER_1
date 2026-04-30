# PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION

context_pack_id: PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION
task_class: MVP4_PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PATCH_RESULT", "SECTION_SCHEMA_VALIDATION", "SECTION_VALIDATOR_DEPENDENCY_CHAIN", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PATCH-RESULT-RUNTIME-SCHEMA-VALIDATION"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "coverage_index_validator", "live_final_guard_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tests/contract/test_patch_result_runtime_schema_validation.py", "tools/run_patch_result_runtime_schema_validators.py", "tools/emit_patch_result_runtime_schema_validation_patch_evidence.py", "system/evidence/audit_reports/PATCH_RESULT_VALIDATOR_RUN_GAP_AUDIT.json", "system/evidence/contract_gaps/PATCH_RESULT_VALIDATOR_RUN_GAP.contract_gap.json", "contracts/generated/context_pack/PATCH_RESULT_RUNTIME_SCHEMA_VALIDATION.md"]

acceptance_checklist:
- patch_result artifacts validate against trader1.patch_result.v1 through the shared schema-instance validator
- live flags remain false and LIVE_ENABLING_PATCH remains forbidden
- validators_required entries must appear in validators_run with usable status, or be explicitly audit-preserved as a historical gap
- historical gaps are not backfilled or rewritten

known_omissions_by_design:
- this patch does not claim live readiness
- this patch does not repair historical evidence by mutating old patch_result semantics

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T00:18:04Z
