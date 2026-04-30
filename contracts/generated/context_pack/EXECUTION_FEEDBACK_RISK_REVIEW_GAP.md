# EXECUTION_FEEDBACK_RISK_REVIEW_GAP

context_pack_id: EXECUTION_FEEDBACK_RISK_REVIEW_GAP
task_class: MVP4_EXECUTION_FEEDBACK_RISK_REVIEW_GAP_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_EXECUTION_FEEDBACK", "SECTION_RISK_EXPOSURE", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-EXECUTION-FEEDBACK-RISK-REVIEW-GAP-HARDENING"]
included_schema_ids: ["trader1.optimizer_feedback_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "execution_feedback_loop_validator", "candidate_scorecard_net_ev_validator", "convergence_assessment_validator", "optimizer_no_live_mutation_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/optimizer_feedback_report.schema.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_optimizer_feedback_validator.py", "tests/validators/fixtures/optimizer_feedback_pass.json", "tests/validators/fixtures/optimizer_feedback_slippage_divergent_fail.json", "tests/validators/fixtures/optimizer_feedback_missing_blocker_fail.json", "tests/validators/fixtures/optimizer_feedback_live_flag_fail.json", "tests/validators/fixtures/optimizer_feedback_missing_risk_review_fail.json", "tools/emit_execution_feedback_risk_review_gap_patch_evidence.py", "contracts/generated/context_pack/EXECUTION_FEEDBACK_RISK_REVIEW_GAP.md", "system/evidence/audit_reports/MVP4_EXECUTION_FEEDBACK_RISK_REVIEW_GAP_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- optimizer feedback cannot become paper-ranking eligible without risk_review_status=PASS
- exposure and drawdown review must PASS before feedback eligibility
- non-PASS risk review must carry a known blocker code and cannot allow paper ranking review
- feedback_hash must match the report payload
- optimizer/convergence feedback remains display-only and cannot create live or scale-up permission

known_omissions_by_design:
- no live exchange data is consumed
- no live order, live config mutation, LIVE_READY snapshot, or LIVE_ENABLING_PATCH is introduced
- no risk scale-up is enabled

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T02:30:32Z
