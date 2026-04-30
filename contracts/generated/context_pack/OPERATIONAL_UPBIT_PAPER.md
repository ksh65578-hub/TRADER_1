# OPERATIONAL_UPBIT_PAPER

context_pack_id: OPERATIONAL_UPBIT_PAPER
task_class: MVP3_OPERATIONAL_UPBIT_PAPER_FOUNDATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP3_LADDER_ACTIVE", "SECTION_MVP3_SCOPE_ACTIVE", "SECTION_MVP3_FOUNDATION_ACTIVE", "SECTION_MVP3_REQUIRED_COMPONENTS_ACTIVE", "SECTION_MVP3_OUTPUT_ARTIFACT_ACTIVE", "SECTION_STAGE_EVIDENCE_PACK_ACTIVE", "SECTION_SIZING_INPUT_ACTIVE", "SECTION_REPLAY_CONSISTENCY_ACTIVE", "SECTION_AGENTS_MVP3_IMPLEMENT_FIRST", "SECTION_AGENTS_MVP3_REQUIRED_FILES"]
included_requirement_ids: ["REQ-MVP3-OPERATIONAL-UPBIT-PAPER-FOUNDATION"]
included_schema_ids: ["trader1.strategy_unit.v1", "trader1.position_sizing_decision.v1", "trader1.replay_consistency_report.v1", "trader1.paper_shadow_separation_report.v1", "trader1.paper_operation_gate_report.v1"]
included_validator_ids: ["upbit_operational_paper_gate_validator"]
included_artifact_ids: ["trader1/runtime/paper/operational_cycle.py", "tests/integration/test_upbit_operational_paper_cycle.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- operational paper remains UPBIT/KRW_SPOT/PAPER scoped
- paper/shadow namespaces are separated
- replay baseline is deterministic for repeated input
- strategy units cannot call order adapters
- sizing uses min-of-caps and cannot submit orders
- dashboard panels are display-only
- stage evidence does not create LIVE_READY
- live flags remain false

known_omissions_by_design:
- no exchange private API call
- no live order submission
- no profitability claim
- no automatic scale-up
- retained archive search results were not used as authority and cannot create permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T15:38:59Z
