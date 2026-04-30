# PARAMETER_EVIDENCE_IDENTITY_JOIN_VALIDATOR

context_pack_id: PARAMETER_EVIDENCE_IDENTITY_JOIN_VALIDATOR
task_class: MVP4_PARAMETER_EVIDENCE_IDENTITY_JOIN_VALIDATOR
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PARAMETER_NARROWING", "SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PARAMETER-EVIDENCE-IDENTITY-JOIN-VALIDATOR"]
included_schema_ids: ["trader1.parameter_narrowing_report.v1"]
included_validator_ids: ["parameter_narrowing_validator", "optimizer_guardrail_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/parameter_narrowing_report.schema.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_parameter_narrowing_validator.py", "tests/validators/fixtures/parameter_narrowing_pass.json", "tests/validators/fixtures/parameter_narrowing_dependency_untested_fail.json", "tests/validators/fixtures/parameter_narrowing_live_flag_fail.json", "tests/validators/fixtures/parameter_narrowing_live_source_fail.json", "tests/validators/fixtures/parameter_narrowing_missing_binding_fail.json", "tests/validators/fixtures/parameter_narrowing_over_narrow_fail.json", "tests/validators/fixtures/parameter_narrowing_warning_fail.json", "tests/validators/fixtures/parameter_narrowing_identity_mismatch_fail.json", "tests/validators/fixtures/parameter_narrowing_identity_stale_fail.json"]

acceptance_checklist:
- Every source_evidence_id has exactly one identity binding.
- Bindings match candidate_id, strategy_id, previous_parameter_hash, proposed_parameter_hash, timeframe_scope, regime_scope, exchange, market_type, and source_modes.
- STALE, TIMEOUT, UNTESTED, BLOCKED, FAIL, duplicate, unknown, missing, or mismatched bindings fail closed.
- Output remains proposal-only; live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- No live order, no credential, no official API verification, no LIVE_READY snapshot, no live config mutation.
- External MVP-5 evidence remains blocked.

conflict_resolution_rule: TRADER_1.md active authority wins. This is read cache only.
generated_at_utc: 2026-04-29T14:51:15Z
