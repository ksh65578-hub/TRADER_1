# EXECUTION_LEDGER

context_pack_id: EXECUTION_LEDGER
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_EVENT_SCHEMA_EXACT", "SECTION_LEDGER_LIVE_BLOCK_RULE", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_AGENTS_EXECUTION_TRUTH_ORDER_PATH", "SECTION_AGENTS_LEDGER_P0_FOUNDATION", "SECTION_AGENTS_SINGLE_WRITER_IDEMPOTENCY"]
included_requirement_ids: ["REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD"]
included_schema_ids: ["trader1.ledger_event.v1", "trader1.validator_result.v1"]
included_validator_ids: ["ledger_durability_validator"]
included_artifact_ids: ["trader1/runtime/ledger/execution_ledger.py", "contracts/schema/ledger_event.schema.json", "tests/runtime/test_execution_ledger.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- ledger events use closed event_type enum
- unknown event type blocks or requires reconciliation
- event_hash tamper fails integrity
- previous_hash chain is append-auditable
- duplicate dedup_key requires reconciliation
- cross-scope ledger chains are blocked
- ledger scaffold cannot submit orders or create live permission

known_omissions_by_design:
- exchange reconciliation adapter
- database transaction writer
- live order API
- private exchange stream
- manual risk-reduction adapter path

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T14:28:53Z
