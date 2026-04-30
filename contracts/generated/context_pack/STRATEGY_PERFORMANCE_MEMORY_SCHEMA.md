# STRATEGY_PERFORMANCE_MEMORY_SCHEMA

context_pack_id: STRATEGY_PERFORMANCE_MEMORY_SCHEMA
task_class: MVP4_STRATEGY_PERFORMANCE_MEMORY_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_STRATEGY_PERFORMANCE_MEMORY", "SECTION_CONVERGENCE_MEMORY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-STRATEGY-PERFORMANCE-MEMORY-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.strategy_performance_memory.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "strategy_performance_memory_validator", "optimizer_memory_state_validator", "optimization_state_validator", "paper_shadow_evidence_accumulation_validator", "failure_analysis_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/strategy_performance_memory.schema.json", "contracts/registry.yaml", "contracts/validators/fixture_catalog.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_strategy_performance_memory_validator.py", "tests/validators/fixtures/strategy_performance_memory_pass.json", "tests/validators/fixtures/strategy_performance_memory_live_flag_fail.json", "tests/validators/fixtures/strategy_performance_memory_raw_pnl_positive_net_negative_fail.json", "tests/validators/fixtures/strategy_performance_memory_insufficient_sample_fail.json", "tests/validators/fixtures/strategy_performance_memory_missing_reason_fail.json", "tests/validators/fixtures/strategy_performance_memory_downtrend_trade_allowed_fail.json", "tests/validators/fixtures/strategy_performance_memory_live_source_mixing_fail.json", "tests/validators/fixtures/strategy_performance_memory_unscoped_fail.json", "tools/run_strategy_performance_memory_validators.py", "tools/emit_strategy_performance_memory_schema_hardening_patch_evidence.py", "contracts/generated/context_pack/STRATEGY_PERFORMANCE_MEMORY_SCHEMA.md", "system/evidence/audit_reports/MVP4_STRATEGY_PERFORMANCE_MEMORY_SCHEMA_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- strategy performance memory uses net EV after fee, spread, slippage, and impact costs
- raw positive PnL cannot be treated as improving when net EV after cost is negative
- paper and shadow source modes remain separated from LIVE
- UPTREND, RANGE, DOWNTREND, and RISK_OFF regime rows are present
- DOWNTREND and RISK_OFF remain no-trade in MVP-4 memory
- entry, exit, and no-trade reasons are visible
- memory cannot create live readiness, live orders, exchange account calls, ACTIVE snapshot mutation, live config mutation, or scale-up permission

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- performance memory is research evidence only, not execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T04:42:54Z
