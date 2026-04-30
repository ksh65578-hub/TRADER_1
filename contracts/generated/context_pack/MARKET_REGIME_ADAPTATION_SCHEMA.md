# MARKET_REGIME_ADAPTATION_SCHEMA

context_pack_id: MARKET_REGIME_ADAPTATION_SCHEMA
task_class: MVP4_MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MARKET_REGIME_ADAPTATION", "SECTION_SYMBOL_REGIME_FIT", "SECTION_CONVERGENCE_MEMORY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-MARKET-REGIME-ADAPTATION-SCHEMA-HARDENING"]
included_schema_ids: ["trader1.market_regime_adaptation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "market_regime_adaptation_validator", "symbol_strategy_regime_fit_validator", "strategy_condition_matrix_validator", "strategy_performance_memory_validator", "paper_shadow_evidence_accumulation_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["contracts/schema/market_regime_adaptation_report.schema.json", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "contracts/validators/fixture_catalog.json", "trader1/validation/mvp0_validators.py", "tests/validators/test_market_regime_adaptation_validator.py", "tests/validators/fixtures/market_regime_adaptation_pass.json", "tests/validators/fixtures/market_regime_adaptation_live_flag_fail.json", "tests/validators/fixtures/market_regime_adaptation_stale_data_entry_fail.json", "tests/validators/fixtures/market_regime_adaptation_risk_off_entry_fail.json", "tests/validators/fixtures/market_regime_adaptation_live_observation_fail.json", "tests/validators/fixtures/market_regime_adaptation_missing_dependency_fail.json", "tests/validators/fixtures/market_regime_adaptation_missing_source_role_fail.json", "tools/run_market_regime_adaptation_validators.py", "tools/emit_market_regime_adaptation_schema_hardening_patch_evidence.py", "contracts/generated/context_pack/MARKET_REGIME_ADAPTATION_SCHEMA.md", "system/evidence/audit_reports/MVP4_MARKET_REGIME_ADAPTATION_SCHEMA_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- market regime adaptation uses fresh, scoped PAPER/SHADOW/READ_ONLY evidence only
- entry review requires symbol-regime fit, strategy condition matrix, and strategy performance memory validator PASS
- stale or missing regime data cannot allow entry
- DOWNTREND and RISK_OFF must block entry and surface REGIME_MISMATCH or RISK_VETO
- live observation, live config mutation, LIVE_READY snapshot writes, execution truth creation, and scale-up are blocked
- dashboard wording says not live_ready and live orders blocked

known_omissions_by_design:
- no live order, credential load, real exchange account call, live observation consumption, live config mutation, or scale-up
- regime adaptation remains analysis evidence only, not execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T04:57:08Z
