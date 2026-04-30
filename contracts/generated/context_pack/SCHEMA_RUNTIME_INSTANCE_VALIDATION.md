# SCHEMA_RUNTIME_INSTANCE_VALIDATION

context_pack_id: SCHEMA_RUNTIME_INSTANCE_VALIDATION
task_class: MVP4_SCHEMA_RUNTIME_INSTANCE_VALIDATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SCHEMA_VALIDATION", "SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SCHEMA-RUNTIME-INSTANCE-VALIDATION"]
included_schema_ids: ["trader1.common_defs.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "closed_enum_validator", "common_defs_drift_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/validation/schema_instance.py", "trader1/validation/mvp0_validators.py", "contracts/schema/common.defs.schema.json", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tests/contract/test_schema_instance_validation.py", "tools/run_runtime_schema_instance_validators.py", "tools/emit_schema_runtime_instance_validation_patch_evidence.py", "contracts/generated/context_pack/SCHEMA_RUNTIME_INSTANCE_VALIDATION.md"]

acceptance_checklist:
- generated runtime instances validate required, enum, const, type, array count, and additionalProperties rules
- unresolved schema refs fail closed
- runtime instances cannot create live_order_ready, live_order_allowed, can_live_trade, or can_submit_order
- dashboard metric count mismatch is covered by a negative test
- common final_decision definition is available to schemas that reference it

known_omissions_by_design:
- this is a scoped MVP-4 schema subset validator, not a full JSON Schema implementation
- no live order, credential, exchange account call, or live burn-in is performed

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T00:07:59Z
