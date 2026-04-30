# VALIDATOR_IMPLEMENTATION

context_pack_id: VALIDATOR_IMPLEMENTATION
task_class: VALIDATOR_IMPLEMENTATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_VALIDATOR_REGISTRY", "SECTION_VALIDATOR_FIXTURES", "SECTION_SCHEMA_CONTRACTS", "SECTION_PATCH_RESULT"]
included_requirement_ids: ["REQ-MVP0-VALIDATOR-SCAFFOLD", "REQ-MVP0-VALIDATOR-LOGIC", "REQ-MVP0-VALIDATOR-FIXTURES"]
included_schema_ids: ["trader1.validator_result.v1", "trader1.validator_fixture_catalog.v1", "trader1.patch_result.v1"]
included_validator_ids: ["authority_integrity_validator", "external_authority_manifest_validator", "registry_validator", "schema_validator", "closed_enum_validator", "common_defs_drift_validator", "patch_result_schema_validator", "coverage_index_validator", "active_schema_extraction_validator", "generated_artifact_dirty_validator", "live_blocked_scaffold_validator"]
included_artifact_ids: ["trader1/validation/mvp0_validators.py", "contracts/validators/fixture_catalog.json", "tests/validators/test_mvp0_validators.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- retained archive is not read by default
- MVP-0 core validators fail closed
- live-blocking fixture set includes PASS, FAIL, and BLOCKED outcomes
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- exact retained archive text
- live-enabling validator PASS claim
- full runtime trading implementation
- optimizer and convergence runtime logic

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
