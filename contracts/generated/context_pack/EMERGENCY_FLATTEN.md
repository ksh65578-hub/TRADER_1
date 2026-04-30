# EMERGENCY_FLATTEN

context_pack_id: EMERGENCY_FLATTEN
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_EMERGENCY_RESOURCE_CLOSURE", "SECTION_RUNTIME_EMERGENCY_REQUIREMENTS", "SECTION_EMERGENCY_FLATTEN_VALIDATOR_ID", "SECTION_LIVE_READINESS_EMERGENCY_BLOCKERS", "SECTION_LIVE_ORDER_PRECHECK_EMERGENCY", "SECTION_AGENTS_RUNTIME_EMERGENCY_RULES", "SECTION_AGENTS_EMERGENCY_MANDATORY_ELEMENTS"]
included_requirement_ids: ["REQ-MVP1-EMERGENCY-FLATTEN-SCAFFOLD"]
included_schema_ids: ["trader1.emergency_flatten_report.v1", "trader1.operator_action_audit.v1", "trader1.validator_result.v1"]
included_validator_ids: ["emergency_flatten_validator"]
included_artifact_ids: ["trader1/runtime/protection/emergency_flatten.py", "contracts/schema/emergency_flatten_report.schema.json", "tests/emergency/test_emergency_flatten_dry_run.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- emergency flatten remains dry-run only in MVP-1
- cancel-all, manual exit, manual reduce, reconciliation, alerting, ledger recording, and futures reduce-only checks are represented
- unavailable emergency protection keeps live_order_ready=false
- orphan position and orphan open order states block readiness
- dry-run actions cannot create entry risk or call an adapter
- live flags remain false

known_omissions_by_design:
- no exchange API call
- no live order submission
- no actual cancel, reduce, or exit execution
- no live emergency protection evidence claim
- retained archive search results were not used as authority and cannot create permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T15:01:03Z
