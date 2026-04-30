# HEARTBEAT

context_pack_id: HEARTBEAT
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_HEARTBEAT_DASHBOARD_TRUTH", "SECTION_MVP1_BOOT_OUTPUTS", "SECTION_OPS_WATCHDOG_HEARTBEAT", "SECTION_AGENTS_HEARTBEAT_FILE"]
included_requirement_ids: ["REQ-MVP1-HEARTBEAT"]
included_schema_ids: ["trader1.heartbeat.v1", "trader1.validator_result.v1"]
included_validator_ids: ["heartbeat_validator"]
included_artifact_ids: ["trader1/runtime/health/heartbeat.py", "contracts/schema/heartbeat.schema.json", "tests/runtime/test_heartbeat.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- heartbeat.json is dashboard serving truth only
- stale heartbeat cannot remain PASS
- component failure cannot remain PASS
- heartbeat cannot set live_order_ready
- heartbeat cannot set live_order_allowed
- heartbeat cannot set can_live_trade
- heartbeat cannot set can_trade

known_omissions_by_design:
- read-only dashboard shell
- summary shell
- root launcher creation
- external watchdog process
- live key loading
- live order API

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:49:02Z
