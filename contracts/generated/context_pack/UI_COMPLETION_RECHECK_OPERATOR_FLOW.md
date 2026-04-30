# UI_COMPLETION_RECHECK_OPERATOR_FLOW

context_pack_id: UI_COMPLETION_RECHECK_OPERATOR_FLOW
task_class: MVP4_UI_COMPLETION_RECHECK_AND_OPERATOR_FLOW_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_OPERATOR_VISIBILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UI-COMPLETION-RECHECK-OPERATOR-FLOW-HARDENING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_ui_completion_recheck_operator_flow_hardening_patch_evidence.py", "contracts/generated/context_pack/UI_COMPLETION_RECHECK_OPERATOR_FLOW.md", "system/evidence/audit_reports/MVP4_UI_COMPLETION_RECHECK_OPERATOR_FLOW_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- first screen shows a four-step operator workflow
- workflow order is RUN_PAPER, INSPECT_DASHBOARD, COLLECT_EVIDENCE, LIVE_REVIEW_BLOCKED
- LIVE_REVIEW_BLOCKED stays blocked and non-current
- workflow steps cannot create live or scale permission
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- workflow display is not execution truth and cannot approve live readiness

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T03:07:34Z
