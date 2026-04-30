# MVP4_PAPER_SHADOW_RUNTIME_SOURCE_REQUIRED_FIELDS

context_pack_id: MVP4_PAPER_SHADOW_RUNTIME_SOURCE_REQUIRED_FIELDS
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PAPER-SHADOW-RUNTIME-SOURCE-REQUIRED-FIELDS"]
included_schema_ids: ["trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "paper_shadow_evidence_accumulation_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/paper_shadow_evidence_accumulation_report.schema.json", "trader1/research/shadow/shadow_runner.py", "trader1/validation/mvp0_validators.py", "tests/validators/test_paper_shadow_evidence_accumulation_validator.py", "tests/validators/fixtures/paper_shadow_evidence_accumulation_pass.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_insufficient_sample_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_stale_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_missing_reason_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_live_flag_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_identity_mismatch_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_identity_stale_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_false_long_run_claim_fail.json", "tools/emit_paper_shadow_runtime_source_required_fields_patch_evidence.py", "contracts/generated/context_pack/MVP4_PAPER_SHADOW_RUNTIME_SOURCE_REQUIRED_FIELDS.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- paper/shadow evidence reports must explicitly carry actual_runtime_source_evidence_ids
- paper/shadow evidence reports must explicitly carry actual_runtime_source_status
- paper/shadow evidence reports must explicitly carry supporting_source_evidence_ids
- legacy or partial reports missing those fields must fail schema identity checks before scorecard eligibility
- all live and scale-up flags remain false

known_omissions_by_design:
- no actual long-run runtime evidence is created
- no exchange account, credential, order-capable endpoint, live order, live config mutation, or scale-up is used
- MVP-5 remains blocked on external evidence and operator approval

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T07:57:02Z
