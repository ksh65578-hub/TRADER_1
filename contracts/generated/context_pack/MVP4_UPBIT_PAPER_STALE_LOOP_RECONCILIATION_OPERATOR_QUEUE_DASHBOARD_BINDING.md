# MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-DASHBOARD-BINDING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "upbit_paper_stale_loop_reconciliation_operator_queue_closure_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py", "tools/emit_upbit_paper_stale_loop_operator_queue_closure_dashboard_binding_patch_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The Upbit PAPER launcher loads the validated stale-loop operator queue closure report.
- The read-only dashboard shows closure status, lane counts, source blocked items, and zero evidence-write counts.
- The closure report is a PASS source artifact for display only and cannot approve portfolio truth, orders, LIVE_READY, or scale-up.
- Operator action remains BLOCKED until the stale-loop reconciliation queue is resolved by later safe tasks.

known_omissions_by_design:
- This patch does not perform ledger recheck, runtime rerun, current-evidence writes, live orders, LIVE_READY, live config mutation, or risk scale-up.
- It binds existing closure evidence into dashboard truth only.

runtime_summary:
- closure_status: BLOCKED
- closure_item_count: 6
- ledger_recheck_ready_count: 5
- recovery_guard_required_count: 1
- current_evidence_write_allowed_count: 0
- current_evidence_usable_after_closure_count: 0
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T05:25:14Z
