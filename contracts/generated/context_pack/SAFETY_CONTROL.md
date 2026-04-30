# SAFETY_CONTROL

context_pack_id: SAFETY_CONTROL
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SURVIVAL_KILL_RESOURCE_RULES", "SECTION_EMERGENCY_RESOURCE_CLOSURE", "SECTION_VALIDATOR_RESOURCE_OPERATOR_IDS", "SECTION_HARD_TRUTH_KILL_RESOURCE_BLOCKERS", "SECTION_AGENTS_RESOURCE_GUARD_TREE", "SECTION_AGENTS_DECISION_RESOURCE_CHECK", "SECTION_AGENTS_P0_KILL_RESOURCE"]
included_requirement_ids: ["REQ-MVP1-KILL-SWITCH-RESOURCE-GUARD"]
included_schema_ids: ["trader1.safety_control_report.v1", "trader1.validator_result.v1"]
included_validator_ids: ["safety_control_validator"]
included_artifact_ids: ["trader1/runtime/resource_guard/safety_control.py", "contracts/schema/safety_control_report.schema.json", "tests/runtime/test_safety_control.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- manual_stop engages kill switch
- kill switch unavailable blocks live readiness
- resource critical blocks new entries
- safety controls cannot call order adapter
- safety controls cannot set live_order_ready
- safety controls cannot set live_order_allowed
- safety controls cannot set can_live_trade

known_omissions_by_design:
- emergency flatten implementation
- live operator approval workflow
- ledger and reconciliation runtime
- live order API
- optimizer runtime
- convergence runtime

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T14:22:22Z
