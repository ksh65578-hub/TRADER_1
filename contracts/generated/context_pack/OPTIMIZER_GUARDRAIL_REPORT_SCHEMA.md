# OPTIMIZER_GUARDRAIL_REPORT_SCHEMA

context_pack_id: OPTIMIZER_GUARDRAIL_REPORT_SCHEMA
task_class: MVP4_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-OPTIMIZER-GUARDRAIL-REPORT-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.optimizer_guardrail_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "optimizer_guardrail_report_validator", "optimizer_run_report_validator", "optimizer_recommendation_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/optimizer_guardrail_report.schema.json", "contracts/registry.yaml", "trader1/validation/mvp0_validators.py", "tests/validators/test_optimizer_guardrail_report_validator.py", "tests/validators/fixtures/optimizer_guardrail_report_pass.json", "tests/validators/fixtures/optimizer_guardrail_report_live_flag_fail.json", "tests/validators/fixtures/optimizer_guardrail_report_dependency_override_fail.json", "tests/validators/fixtures/optimizer_guardrail_report_live_ready_wording_fail.json", "tests/validators/fixtures/optimizer_guardrail_report_missing_blocker_fail.json", "tests/validators/fixtures/optimizer_guardrail_report_live_writer_fail.json", "tests/validators/fixtures/optimizer_guardrail_report_scale_up_fail.json", "tools/run_optimizer_guardrail_report_validators.py", "tools/run_optimizer_run_guardrail_validators.py", "tools/run_optimizer_recommendation_validators.py", "tools/emit_optimizer_guardrail_report_schema_hardening_patch_evidence.py", "contracts/generated/context_pack/OPTIMIZER_GUARDRAIL_REPORT_SCHEMA.md", "system/evidence/audit_reports/MVP4_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- optimizer guardrail PASS cannot be read as LIVE_READY
- optimizer guardrail PASS cannot override FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT dependencies
- optimizer guardrail report cannot write live snapshots, mutate live config, submit orders, call exchange accounts, or recommend scale-up
- blocked guardrail reports carry explicit blocker evidence
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- guardrail reports remain display/evidence artifacts only

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T04:07:18Z
