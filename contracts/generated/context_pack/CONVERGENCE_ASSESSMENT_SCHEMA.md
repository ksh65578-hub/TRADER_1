# CONVERGENCE_ASSESSMENT_SCHEMA

context_pack_id: CONVERGENCE_ASSESSMENT_SCHEMA
task_class: MVP4_CONVERGENCE_ASSESSMENT_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_CONVERGENCE_ASSESSMENT", "SECTION_MODEL_DRIFT", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-CONVERGENCE-ASSESSMENT-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.convergence_assessment_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "convergence_assessment_validator", "convergence_objective_profile_validator", "optimizer_memory_state_validator", "strategy_performance_memory_validator", "overfit_diagnostic_validator", "execution_feedback_loop_validator", "failure_analysis_validator", "paper_shadow_evidence_accumulation_validator", "market_regime_adaptation_validator", "model_drift_validator", "coverage_index_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/convergence_assessment_report.schema.json", "contracts/validators/fixture_catalog.json", "contracts/validators/validator_registry.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_convergence_assessment_validator.py", "tests/validators/fixtures/convergence_assessment_pass.json", "tests/validators/fixtures/convergence_assessment_live_flag_fail.json", "tests/validators/fixtures/convergence_assessment_missing_dependency_fail.json", "tests/validators/fixtures/convergence_assessment_untested_dependency_fail.json", "tests/validators/fixtures/convergence_assessment_drift_unblocked_fail.json", "tests/validators/fixtures/convergence_assessment_writer_input_fail.json", "tests/validators/fixtures/convergence_assessment_scale_up_fail.json", "tools/run_convergence_assessment_validators.py", "tools/emit_convergence_assessment_schema_hardening_patch_evidence.py", "contracts/generated/context_pack/CONVERGENCE_ASSESSMENT_SCHEMA.md", "system/evidence/audit_reports/MVP4_CONVERGENCE_ASSESSMENT_SCHEMA_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- convergence assessment report includes all required dependency statuses
- parent assessment cannot pass over FAIL, BLOCKED, UNTESTED, STALE, or TIMEOUT dependencies
- failure analysis, paper/shadow evidence accumulation, model drift, and coverage dependencies are represented
- stale data, model drift, writer input eligibility, and scale-up attempts fail closed
- dashboard/operator wording says not live_ready and live orders blocked
- all live/scale/mutation fields stay false

known_omissions_by_design:
- no live order, credential load, real exchange account call, LIVE_READY writer input, live config mutation, or scale-up
- convergence assessment remains analysis evidence only, not execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T05:19:52Z
