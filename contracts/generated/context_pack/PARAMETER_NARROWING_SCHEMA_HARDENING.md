# PARAMETER_NARROWING_SCHEMA_HARDENING

context_pack_id: PARAMETER_NARROWING_SCHEMA_HARDENING
task_class: MVP4_PARAMETER_NARROWING_SCHEMA_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PARAMETER_NARROWING", "SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PARAMETER-NARROWING-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.parameter_narrowing_report.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "parameter_narrowing_validator", "optimizer_guardrail_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "live_final_guard_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/parameter_narrowing_report.schema.json", "trader1/validation/mvp0_validators.py", "tools/run_optimizer_convergence_guardrail_validators.py", "tests/validators/test_parameter_narrowing_validator.py", "tests/validators/fixtures/parameter_narrowing_pass.json", "tests/validators/fixtures/parameter_narrowing_dependency_untested_fail.json", "tests/validators/fixtures/parameter_narrowing_over_narrow_fail.json", "tests/validators/fixtures/parameter_narrowing_live_flag_fail.json", "tests/validators/fixtures/parameter_narrowing_live_source_fail.json", "tests/validators/fixtures/parameter_narrowing_warning_fail.json", "tools/emit_parameter_narrowing_schema_hardening_patch_evidence.py", "system/evidence/audit_reports/MVP4_PARAMETER_NARROWING_SCHEMA_HARDENING_20260429.md", "contracts/generated/context_pack/PARAMETER_NARROWING_SCHEMA_HARDENING.md"]

acceptance_checklist:
- Parameter narrowing is a PAPER proposal only.
- Dependency closure, paper/shadow sample counts, and over-narrowing limits are validated.
- Live config mutation, active snapshot mutation, order submission, exchange account calls, and scale-up remain false.
- Negative fixtures cover dependency UNTESTED, over-narrowing, live flag drift, live source mixing, and weak operator warning.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T06:04:32Z
