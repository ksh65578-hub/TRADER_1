# CONFIG_VALIDATION

context_pack_id: CONFIG_VALIDATION
task_class: MVP0_CONTRACT_BASELINE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_CONFIG_VALIDATION", "SECTION_HARD_TRUTH_CONFIG_FIELDS", "SECTION_TEST_LANES_CONFIG_SCHEMA", "SECTION_AGENTS_CONFIG_VALIDATION"]
included_requirement_ids: ["REQ-MVP0-CONFIG-VALIDATION"]
included_schema_ids: ["trader1.runtime_config.v1", "trader1.validator_result.v1"]
included_validator_ids: ["runtime_config_validator"]
included_artifact_ids: ["contracts/schema/runtime_config.schema.json", "trader1/config/config_schema.py", "tests/config/test_config_validation.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- runtime config includes schema_id, exchange, market_type, mode, session_id, registry_hash, and config_hash
- exchange, market_type, and mode are registry-backed closed values
- UPBIT config is scoped to KRW_SPOT
- BINANCE config requires explicit SPOT or FUTURES_USDT_M selection
- market_type cannot be an implicit default
- config schema test lane exists
- config invalid remains a live-blocking condition
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- startup probe execution
- real exchange credential loading
- LIVE_READY snapshot writer
- live preflight

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:24:49Z
