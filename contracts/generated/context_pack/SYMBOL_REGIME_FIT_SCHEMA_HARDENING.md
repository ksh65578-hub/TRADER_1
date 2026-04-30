# SYMBOL_REGIME_FIT_SCHEMA_HARDENING

context_pack_id: SYMBOL_REGIME_FIT_SCHEMA_HARDENING
task_class: MVP4_SYMBOL_REGIME_FIT_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SYMBOL_SELECTION_REGIME", "SECTION_REGIME_FIT", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SYMBOL-REGIME-FIT-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.symbol_strategy_regime_fit_report.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "symbol_strategy_regime_fit_validator", "strategy_condition_matrix_validator", "candidate_scorecard_net_ev_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "optimizer_no_live_mutation_validator", "profitability_optimizer_evidence_gap_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/symbol_strategy_regime_fit_report.schema.json", "trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tests/validators/test_symbol_strategy_regime_fit_validator.py", "tests/validators/fixtures/symbol_strategy_regime_fit_pass.json", "tests/validators/fixtures/symbol_strategy_regime_fit_low_liquidity_fail.json", "tests/validators/fixtures/symbol_strategy_regime_fit_live_flag_fail.json", "tests/validators/fixtures/symbol_strategy_regime_fit_missing_family_fail.json", "tools/run_symbol_strategy_regime_fit_validators.py", "tools/emit_symbol_strategy_regime_fit_schema_hardening_patch_evidence.py", "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json", "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json", "contracts/generated/context_pack/SYMBOL_REGIME_FIT_SCHEMA_HARDENING.md"]

acceptance_checklist:
- symbol-regime report requires liquidity, volatility, spread, depth, and regime fields
- every strategy family is explicitly supported or rejected
- paper review eligibility requires metrics above thresholds and no blockers
- RISK_OFF reports cannot become paper review eligible
- report cannot carry live readiness, live order permission, live trading permission, scale-up, or promotion eligibility

known_omissions_by_design:
- no optimizer runtime promotion
- no live config mutation
- no LIVE_READY snapshot write
- no risk scale-up
- OOS robustness, execution feedback, and convergence memory remain open contract_gap work

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T01:02:21Z
