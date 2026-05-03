# MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_RUNTIME_DEPTH_DASHBOARD_BINDING

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_RUNTIME_DEPTH_DASHBOARD_BINDING
task_class: MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_DASHBOARD_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH-RUNTIME-DEPTH-DASHBOARD-BINDING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_post_rerun_reconciliation_repair_path_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "contracts/schema/upbit_paper_post_rerun_reconciliation_repair_path_report.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py", "trader1/runtime/boot/safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py", "tests/runtime/test_safe_launcher.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_repair_path_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_post_rerun_reconciliation_repair_path_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_RUNTIME_DEPTH_DASHBOARD_BINDING.md"]

acceptance_checklist:
- The Upbit PAPER dashboard loads the validated post-rerun reconciliation repair path report.
- The repair path preserves the closure recheck runtime-depth binding from persistent loop, public data, feature snapshot, strategy/regime/cost linkage, and mismatch-count evidence.
- The repair path is displayed as dashboard truth only, not current evidence, execution truth, or live readiness.
- Repair gate count, satisfied count, blocked count, first gate, source bindings, runtime-depth status, and zero write allowance are visible.
- Portfolio cash/equity stay UNVERIFIED while repair gates are blocked, even when configured PAPER capital is 1,000,000 KRW.
- Current evidence writes, live orders, and scale-up remain blocked.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, LIVE_READY patch, live config mutation, or scale-up patch.
- It does not resolve POST_RERUN_RECONCILIATION_REQUIRED; it makes the blocked repair path operator-visible.
- No private exchange/account/API call, credential, live order, or risk scale-up was used.

runtime_summary:
- dashboard_blocking_reason: AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED
- operator_action_status: BLOCKED
- repair_path_status: BLOCKED_REPAIR_PATH_DECLARED
- repair_gate_count: 4
- satisfied_repair_gate_count: 0
- blocked_repair_gate_count: 4
- source_closure_status: CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED
- source_recheck_status: BLOCKED_POST_RERUN_CLOSURE_CONFIRMED
- source_recheck_runtime_depth_status: PASS
- source_recheck_runtime_depth_mismatch_count: 0
- source_recheck_persistent_loop_validation_status: PASS
- current_evidence_write_allowed: false
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-03T14:30:57Z
