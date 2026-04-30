# CANDIDATE_SCORECARD_LIVE_SEPARATION

context_pack_id: CANDIDATE_SCORECARD_LIVE_SEPARATION
task_class: MVP4_CANDIDATE_SCORECARD_LIVE_SEPARATION_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_STRATEGY_EVIDENCE", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-CANDIDATE-SCORECARD-LIVE-SEPARATION-HARDENING"]
included_schema_ids: ["trader1.candidate_scorecard.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "candidate_scorecard_net_ev_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/candidate_scorecard.schema.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_candidate_scorecard_net_ev_validator.py", "tests/validators/fixtures/candidate_scorecard_net_ev_pass.json", "tests/validators/fixtures/candidate_scorecard_net_ev_raw_cost_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_live_flag_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_missing_oos_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_live_ready_wording_fail.json", "tools/emit_candidate_scorecard_live_separation_hardening_patch_evidence.py", "contracts/generated/context_pack/CANDIDATE_SCORECARD_LIVE_SEPARATION.md", "system/evidence/audit_reports/MVP4_CANDIDATE_SCORECARD_LIVE_SEPARATION_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- candidate scorecard artifact is structurally marked as PAPER scorecard input only
- ranking_eligible cannot imply LIVE_READY or scale-up permission
- misleading LIVE_READY wording in scorecard warnings is rejected
- optimizer and convergence guardrails continue to pass/block safely after schema hardening
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- candidate scorecards remain optimizer input only and cannot approve live readiness

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T03:38:01Z
