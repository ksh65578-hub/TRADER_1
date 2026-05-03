# MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION_OPERATOR_UX_RECHECK

context_pack_id: MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION_OPERATOR_UX_RECHECK
task_class: MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION_OPERATOR_UX_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION-OPERATOR-UX-RECHECK"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_post_repair_reconciliation_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_upbit_paper_post_repair_reconciliation_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION_OPERATOR_UX_RECHECK.md"]

acceptance_checklist:
- The Upbit PAPER dashboard loads the validated post-repair reconciliation report.
- The primary operator action says "Inspect post-repair reconciliation" instead of a generic blocker label.
- The workflow summary explains that current evidence and portfolio truth writes remain blocked.
- The post-repair repair candidate remains dashboard truth only, not current evidence, execution truth, LIVE_READY, or live permission.
- Candidate count, hash mismatch count, operator-action count, and zero current-evidence usable count are visible.
- Portfolio cash/equity stay UNVERIFIED while post-repair reconciliation is blocked.
- Current evidence writes, live orders, and scale-up remain blocked.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, LIVE_READY patch, live config mutation, or scale-up patch.
- It does not resolve POST_REPAIR_RECONCILIATION_REQUIRED; it makes the blocked post-repair status operator-visible.
- No private exchange/account/API call, credential, live order, or risk scale-up was used.

runtime_summary:
- dashboard_blocking_reason: POST_REPAIR_RECONCILIATION_REQUIRED
- operator_action_status: BLOCKED
- operator_action_label: Inspect post-repair reconciliation
- operator_workflow_status: BLOCKED
- operator_workflow_current_step: INSPECT_DASHBOARD
- post_repair_reconciliation_status: BLOCKED
- repair_candidate_count: 1
- reconciliation_item_count: 1
- source_loop_expected_rollup_hash_mismatch_count: 1
- candidate_current_evidence_usable_count: 0
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-03T15:49:46Z
