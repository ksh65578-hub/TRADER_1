# OPTIMIZER_RUN_GUARDRAIL_SCHEMA

context_pack_id: OPTIMIZER_RUN_GUARDRAIL_SCHEMA
task_class: MVP4_OPTIMIZER_RUN_GUARDRAIL_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-OPTIMIZER-RUN-GUARDRAIL-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.optimizer_run_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "optimizer_run_report_validator", "optimizer_recommendation_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/optimizer_run_report.schema.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_optimizer_run_report_validator.py", "tests/validators/fixtures/optimizer_run_pass.json", "tests/validators/fixtures/optimizer_run_live_flag_fail.json", "tests/validators/fixtures/optimizer_run_live_mode_fail.json", "tests/validators/fixtures/optimizer_run_live_ready_wording_fail.json", "tests/validators/fixtures/optimizer_run_missing_blocker_fail.json", "tests/validators/fixtures/optimizer_run_live_writer_fail.json", "tests/validators/fixtures/optimizer_run_raw_pnl_objective_fail.json", "tools/run_optimizer_run_guardrail_validators.py", "tools/run_optimizer_recommendation_validators.py", "tools/emit_optimizer_run_guardrail_schema_hardening_patch_evidence.py", "contracts/generated/context_pack/OPTIMIZER_RUN_GUARDRAIL_SCHEMA.md", "system/evidence/audit_reports/MVP4_OPTIMIZER_RUN_GUARDRAIL_SCHEMA_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- optimizer run report is not a generic status artifact
- optimizer run report must be REPLAY/PAPER/SHADOW/READ_ONLY scoped before live-enabling evidence
- optimizer run report must use NET_EV_AFTER_COST for candidate ranking input
- optimizer run report cannot submit orders, call exchange accounts, write LIVE_READY, mutate live config, or scale up
- blocked, stale, resource-blocked, or recovery-blocked optimizer runs carry explicit blockers
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- optimizer output remains analysis/ranking input only and cannot approve live readiness

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T03:57:16Z
