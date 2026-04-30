# MVP4_OPTIMIZER_CONFIG_OBJECTIVE_RANKING_VALIDATORS

context_pack_id: MVP4_OPTIMIZER_CONFIG_OBJECTIVE_RANKING_VALIDATORS
task_class: MVP4_REGISTERED_VALIDATOR_BACKLOG_TRIAGE_CONTINUE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_OPTIMIZER_CORE", "SECTION_VALIDATOR_IMPLEMENTATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-OPTIMIZER-CONFIG-OBJECTIVE-RANKING-VALIDATORS"]
included_schema_ids: ["trader1.profit_optimizer_config.v1", "trader1.optimizer_run_report.v1"]
included_validator_ids: ["profit_optimizer_config_validator", "objective_function_validator", "candidate_ranking_validator"]
included_artifact_ids: ["contracts/schema/profit_optimizer_config.schema.json", "tests/validators/test_profit_optimizer_config_validator.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- optimizer objective basis is NET_EV_AFTER_COST only
- cost stack includes fee, spread, slippage, impact, and latency
- candidate ranking emits CANDIDATE_RANKING_INPUT only from non-live evidence
- optimizer config cannot grant live permission, write LIVE_READY, call exchange accounts, or scale up
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live account data
- no live order test
- no parameter promotion to live config

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This generated pack is not authority.
generated_at_utc: 2026-04-29T12:38:08Z
