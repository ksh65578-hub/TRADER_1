# MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_DASHBOARD_BINDING

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_DASHBOARD_BINDING
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_DASHBOARD_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-DASHBOARD-BINDING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py", "tools/emit_upbit_paper_stale_loop_post_regeneration_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_DASHBOARD_BINDING.md"]

acceptance_checklist:
- The Upbit PAPER dashboard loads the validated stale-loop post-regeneration reconciliation report.
- Accepted current-schema regenerated artifacts are visible as accepted but remain separated from portfolio truth.
- Blocked regenerated replacements remain excluded from current evidence until ledger/recovery reconciliation is resolved.
- Portfolio cash/equity stay UNVERIFIED while stale-loop post-regeneration reconciliation is blocked.
- Current evidence writes, live orders, and scale-up remain blocked.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, LIVE_READY patch, live config mutation, or scale-up patch.
- It does not resolve STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED; it makes the blocked post-regeneration state operator-visible.
- No private exchange/account/API call, credential, live order, or risk scale-up was used.

runtime_summary:
- dashboard_blocking_reason: STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED
- operator_action_status: BLOCKED
- post_reconciliation_status: BLOCKED
- post_reconciliation_item_count: 16
- planned_regeneration_item_count: 16
- regenerated_current_accepted_count: 10
- regenerated_current_blocked_reconciliation_count: 6
- current_evidence_usable_count: 10
- excluded_from_current_evidence_count: 6
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T00:58:20Z
