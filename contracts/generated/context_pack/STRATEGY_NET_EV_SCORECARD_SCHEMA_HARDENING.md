# STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING

context_pack_id: STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING
task_class: MVP4_STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_OPTIMIZER_OBJECTIVE", "SECTION_STRATEGY_PROFITABILITY", "SECTION_EXECUTION_COST_MODEL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-STRATEGY-NET-EV-SCORECARD-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.candidate_scorecard.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "candidate_scorecard_net_ev_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "optimizer_no_live_mutation_validator", "profitability_optimizer_evidence_gap_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/candidate_scorecard.schema.json", "trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tests/validators/test_candidate_scorecard_net_ev_validator.py", "tests/validators/fixtures/candidate_scorecard_net_ev_pass.json", "tests/validators/fixtures/candidate_scorecard_net_ev_raw_cost_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_live_flag_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_missing_oos_fail.json", "tools/run_candidate_scorecard_net_ev_validators.py", "tools/emit_strategy_net_ev_scorecard_schema_hardening_patch_evidence.py", "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json", "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json", "contracts/generated/context_pack/STRATEGY_NET_EV_SCORECARD_SCHEMA_HARDENING.md"]

acceptance_checklist:
- candidate_scorecard requires NET_EV_AFTER_COST objective basis
- fee, spread, slippage, impact, and latency cost fields are required
- ranking eligibility requires net EV above minimum and robustness PASS/LOW status
- scorecard artifacts cannot carry live or scale-up permission
- raw positive edge below cost-adjusted threshold fails closed

known_omissions_by_design:
- no optimizer runtime promotion
- no live config mutation
- no LIVE_READY snapshot write
- no risk scale-up
- strategy condition matrix and convergence memory maturity remain open contract_gap work

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T00:45:18Z
