# ROOT_LAUNCHER_GUARD

context_pack_id: ROOT_LAUNCHER_GUARD
task_class: MVP0_CONTRACT_BASELINE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_ROOT_LAUNCHER", "SECTION_AGENTS_ROOT_LAUNCHER", "SECTION_LIVE_GATE", "SECTION_ORDER_PATH"]
included_requirement_ids: ["REQ-MVP0-ROOT-LAUNCHER-GUARD"]
included_schema_ids: ["trader1.validator_result.v1"]
included_validator_ids: ["root_launcher_guard_validator"]
included_artifact_ids: ["trader1/runtime/boot/launcher_guard.py", "tests/contract/test_root_launchers.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

current_root_launchers_found: []
unexpected_root_launchers_found: []
live_order_path_found: false
direct_strategy_to_exchange_call_found: false

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- root launcher names are UPBIT_PAPER, UPBIT_LIVE, BINANCE_PAPER, BINANCE_LIVE only
- dashboard, debug, test, temporary, duplicate, exchange-ambiguous, and mode-ambiguous root launchers are blocked
- paper launchers do not load live credentials or call live order APIs
- live launchers do not use paper broker
- Binance launchers require explicit market_type selection
- Binance futures live is not an implicit default
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- MVP-1 creation of the four root launchers
- live-enabling evidence
- real exchange credentials
- manual order test

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:17:17Z
