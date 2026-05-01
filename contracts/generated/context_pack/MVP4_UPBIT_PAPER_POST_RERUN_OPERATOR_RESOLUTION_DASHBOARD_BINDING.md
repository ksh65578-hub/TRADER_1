# MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_DASHBOARD_BINDING

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_DASHBOARD_BINDING
task_class: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_DASHBOARD_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-DASHBOARD-BINDING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_post_rerun_operator_resolution_audit_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator", "upbit_paper_post_rerun_operator_reconciliation_review_guidance_validator", "upbit_paper_post_rerun_operator_resolution_audit_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_post_rerun_operator_resolution_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_DASHBOARD_BINDING.md"]

acceptance_checklist:
- The Upbit PAPER dashboard loads validated post-rerun operator resolution audit as display-only dashboard truth.
- POST_RERUN_RECONCILIATION_REQUIRED remains the dashboard blocking reason and operator primary blocker.
- Resolution status, unresolved/resolved counts, control counts, zero current-evidence writes, and source binding status are visible.
- The operator action is BLOCKED/STOP_AND_INSPECT and safe_to_continue_paper=false.
- Current evidence writes, live orders, and scale-up remain blocked.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, LIVE_READY patch, live config mutation, or scale-up patch.
- It does not resolve POST_RERUN_RECONCILIATION_REQUIRED; it makes the unresolved resolution audit operator-visible.
- No private exchange/account/API call, credential, live order, or risk scale-up was used.

runtime_summary:
- dashboard_blocking_reason: POST_RERUN_RECONCILIATION_REQUIRED
- operator_action_status: BLOCKED
- resolution_audit_status: UNRESOLVED_RECONCILIATION_REVIEW_ONLY
- unresolved_item_count: 8
- resolved_item_count: 0
- resolution_control_count: 4
- resolution_controls_satisfied_count: 0
- current_evidence_write_allowed_count: 0
- source_review_guidance_file_load_status: PASS
- source_decision_audit_file_load_status: PASS
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T20:41:11Z
