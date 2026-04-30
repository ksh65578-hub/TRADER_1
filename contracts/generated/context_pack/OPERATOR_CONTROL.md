# OPERATOR_CONTROL

context_pack_id: OPERATOR_CONTROL
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_OPERATOR_ACTION_AUDIT_SCHEMA_EXACT", "SECTION_OPERATOR_CONTROL_ACTIVE_RULES", "SECTION_OPERATOR_CONTROL_VALIDATOR_IDS", "SECTION_CORE_MANUAL_BYPASS_RULE", "SECTION_AGENTS_OPERATOR_CONTROL_RULES"]
included_requirement_ids: ["REQ-MVP1-OPERATOR-CONTROL-AUDIT"]
included_schema_ids: ["trader1.operator_action_audit.v1", "trader1.validator_result.v1"]
included_validator_ids: ["operator_action_audit_validator", "operator_control_validator"]
included_artifact_ids: ["trader1/runtime/operator_control/operator_control.py", "contracts/schema/operator_action_audit.schema.json", "tests/runtime/test_operator_control.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- manual controls produce an audit record
- high-risk controls require explicit confirmation and scope
- manual_stop forces a kill-switch blocked audit
- manual_resume_read_only cannot resume live mode
- manual reduce/exit remains blocked without adapter, ledger, and reconciliation evidence
- manual action cannot create live_order_ready, live_order_allowed, can_live_trade, or can_submit_order

known_omissions_by_design:
- no live order adapter call
- no emergency flatten execution
- no operator UI
- no exchange reconciliation adapter
- retained archive was read only for omitted-detail lookup and cannot create permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T14:39:08Z
