# CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING

context_pack_id: CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING
task_class: MVP4_CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_CONVERGENCE_MEMORY", "SECTION_FAILURE_ANALYSIS", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-CONVERGENCE-MEMORY-FAILURE-LEARNING-HARDENING"]
included_schema_ids: ["trader1.failure_analysis_report.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "failure_analysis_validator", "execution_feedback_loop_validator", "overfit_diagnostic_validator", "candidate_scorecard_net_ev_validator", "strategy_condition_matrix_validator", "symbol_strategy_regime_fit_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "optimizer_no_live_mutation_validator", "profitability_optimizer_evidence_gap_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/failure_analysis_report.schema.json", "trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tests/validators/test_failure_analysis_validator.py", "tests/validators/fixtures/failure_analysis_pass.json", "tests/validators/fixtures/failure_analysis_unknown_root_live_affecting_fail.json", "tests/validators/fixtures/failure_analysis_repeated_unblocked_fail.json", "tests/validators/fixtures/failure_analysis_live_flag_fail.json", "tools/run_failure_analysis_validators.py", "tools/emit_convergence_memory_failure_learning_hardening_patch_evidence.py", "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json", "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json", "contracts/generated/context_pack/CONVERGENCE_MEMORY_FAILURE_LEARNING_HARDENING.md"]

acceptance_checklist:
- failure analysis requires known/unknown root-cause status and source evidence ids
- unknown live-affecting root cause blocks live order, promotion, and ranking
- repeated same-root-cause failures block ranking/promotion and require previous failure links
- memory-write-required analysis must be append-only recorded
- report remains dashboard/display truth only and cannot create live readiness, live order permission, promotion, or scale-up

known_omissions_by_design:
- no live execution feedback collection
- no optimizer runtime promotion
- no LIVE_READY snapshot write
- no risk scale-up
- runtime convergence memory accumulation, paper/shadow accumulation, dashboard profitability maturity, and risk exposure quality remain open contract_gap work

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T01:34:04Z
