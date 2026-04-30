# ORDER_PATH_GUARD

context_pack_id: ORDER_PATH_GUARD
task_class: MVP0_CONTRACT_BASELINE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_ORDER_PATH", "SECTION_LIVE_GATE", "SECTION_PATCH_RESULT"]
included_requirement_ids: ["REQ-MVP0-ORDER-PATH-GUARD"]
included_schema_ids: ["trader1.validator_result.v1", "trader1.patch_result.v1"]
included_validator_ids: ["single_writer_order_path_validator", "strategy_direct_order_validator"]
included_artifact_ids: ["trader1/execution/live_order_gateway.py", "tests/live_blocked/test_order_path_guard.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- strategy signals cannot call exchange APIs or order adapters directly
- FinalDecision without LIVE_READY evidence blocks before adapter submit
- ambiguous submit state requires same-identifier reconciliation before any new order
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- real order adapter implementation
- live-enabling evidence
- exchange credentials
- live order submission

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:01:35Z
