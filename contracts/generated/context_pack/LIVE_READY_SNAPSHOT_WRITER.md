# LIVE_READY_SNAPSHOT_WRITER

context_pack_id: LIVE_READY_SNAPSHOT_WRITER
task_class: LIVE_BLOCKED_TEST
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LIVE_READY_WRITER_GUARD", "SECTION_LIVE_READY_SNAPSHOT_SCHEMA", "SECTION_LIVE_READY_WRITER_INPUT_SCHEMA", "SECTION_AGENTS_LIVE_READY_WRITER_GUARD"]
included_requirement_ids: ["REQ-MVP0-LIVE-READY-SNAPSHOT-WRITER-GUARD"]
included_schema_ids: ["trader1.live_ready_snapshot.v1", "trader1.live_ready_candidate_writer_input.v1", "trader1.validator_result.v1"]
included_validator_ids: ["live_ready_snapshot_writer_validator"]
included_artifact_ids: ["trader1/runtime/readiness/live_ready_snapshot.py", "tests/readiness/test_live_ready_snapshot_writer.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- LIVE_READY_CANDIDATE_WRITER_INPUT is not a LIVE_READY snapshot
- Stage B PASS is not a LIVE_READY snapshot
- missing evidence manifest blocks snapshot generation
- stale, untested, timeout, or failed validator results block snapshot generation
- scope mismatch blocks snapshot generation
- live_order_allowed snapshot requires official API, burn-in, emergency, manual/operator evidence, PASS rollup, and no invalidation
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- LIVE_ENABLING_PATCH
- operator approval
- official API verification
- manual order test
- read-only burn-in
- actual LIVE_READY snapshot write

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:33:33Z
