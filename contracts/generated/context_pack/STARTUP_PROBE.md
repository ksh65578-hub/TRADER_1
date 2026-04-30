# STARTUP_PROBE

context_pack_id: STARTUP_PROBE
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP1_SAFE_BOOT_SCOPE", "SECTION_STARTUP_PROBE_TRUTH_SURFACE", "SECTION_HARD_TRUTH_STARTUP_PROBE", "SECTION_ENGINE_STARTUP_PRINCIPLE", "SECTION_AGENTS_MVP1_SAFE_BOOT_FILES"]
included_requirement_ids: ["REQ-MVP1-STARTUP-PROBE"]
included_schema_ids: ["trader1.startup_probe.v1", "trader1.validator_result.v1"]
included_validator_ids: ["startup_probe_validator"]
included_artifact_ids: ["trader1/runtime/boot/startup_probe.py", "contracts/schema/startup_probe.schema.json", "tests/runtime/test_startup_probe.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- startup_probe.json is dashboard serving truth only
- missing hard truth blocks startup and trade
- startup_probe PASS alone does not permit trading
- RUNNING before startup_probe PASS is blocked
- startup probe cannot set live_order_ready
- startup probe cannot set live_order_allowed
- startup probe cannot set can_live_trade

known_omissions_by_design:
- heartbeat emitter
- summary shell
- root launcher creation
- ledger/WAL implementation
- live key loading
- live order API

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:40:46Z
