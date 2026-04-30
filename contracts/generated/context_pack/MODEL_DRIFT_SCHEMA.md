# MODEL_DRIFT_SCHEMA

context_pack_id: MODEL_DRIFT_SCHEMA
task_class: MVP4_MODEL_DRIFT_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MODEL_DRIFT", "SECTION_CONVERGENCE_ASSESSMENT", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-MODEL-DRIFT-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.model_drift_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "model_drift_validator", "overfit_diagnostic_validator", "execution_feedback_loop_validator", "failure_analysis_validator", "paper_shadow_evidence_accumulation_validator", "market_regime_adaptation_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/model_drift_report.schema.json", "contracts/validators/fixture_catalog.json", "contracts/validators/validator_registry.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_model_drift_validator.py", "tests/validators/fixtures/model_drift_pass.json", "tests/validators/fixtures/model_drift_live_flag_fail.json", "tests/validators/fixtures/model_drift_detected_claim_fail.json", "tests/validators/fixtures/model_drift_suspected_unblocked_fail.json", "tests/validators/fixtures/model_drift_missing_baseline_fail.json", "tests/validators/fixtures/model_drift_stale_input_fail.json", "tests/validators/fixtures/model_drift_scale_up_fail.json", "tools/run_model_drift_validators.py", "tools/emit_model_drift_schema_hardening_patch_evidence.py", "contracts/generated/context_pack/MODEL_DRIFT_SCHEMA.md", "system/evidence/audit_reports/MVP4_MODEL_DRIFT_SCHEMA_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- model drift reports use REPLAY/PAPER/SHADOW/READ_ONLY evidence only
- stale or missing drift input cannot keep robust convergence claims
- DRIFT_SUSPECTED, DRIFT_DETECTED, and BLOCKED states require promotion blocking and blocker evidence
- NO_DRIFT requires fresh data, baseline/evaluation sample floors, and drift_score within threshold
- scale-up, live permission, live config mutation, LIVE_READY snapshot writes, and ACTIVE snapshot mutation are blocked
- dashboard/operator wording says not live_ready and live orders blocked

known_omissions_by_design:
- no live order, credential load, real exchange account call, live observation consumption, live config mutation, or scale-up
- model drift remains analysis evidence only, not execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T05:07:29Z
