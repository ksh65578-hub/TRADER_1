# LIVE_BLOCKED_TEST

context_pack_id: LIVE_BLOCKED_TEST
task_class: LIVE_BLOCKED_TEST
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LIVE_GATE", "SECTION_LIVE_READY_WRITER_GUARD", "SECTION_LIVE_FINAL_GUARD", "SECTION_LIVE_BLOCKED_TESTS", "SECTION_VALIDATOR_FIXTURES"]
included_requirement_ids: ["REQ-MVP0-LIVE-BLOCKED-TEST", "REQ-MVP0-LIVE-BLOCKED-MATRIX"]
included_schema_ids: ["trader1.validator_result.v1", "trader1.patch_result.v1"]
included_validator_ids: ["live_blocked_negative_matrix_validator", "live_blocked_scaffold_validator"]
included_artifact_ids: ["trader1/safety/live_order_gate.py", "tests/live_blocked/fixtures/live_blocked_matrix.json", "tests/live_blocked/test_live_blocked_scaffold.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- retained archive is not read by default
- all required live-blocked cases keep expected_order_adapter_called=false
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- live-enabling evidence
- real exchange credentials
- manual order test
- read-only burn-in
- full runtime trading implementation

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T12:43:48Z
