# MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_DASHBOARD_BINDING

context_pack_id: MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_DASHBOARD_BINDING
task_class: MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_DASHBOARD_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER-PRECHECK-DASHBOARD-BINDING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_repaired_current_evidence_audited_writer_precheck_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_repaired_current_evidence_audited_writer_precheck_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_upbit_paper_repaired_current_evidence_audited_writer_precheck_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_PRECHECK_DASHBOARD_BINDING.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repaired_current_evidence_audited_writer_precheck_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html"]

acceptance_checklist:
- The read-only dashboard loads the audited writer precheck source.
- The first-screen operator action names the audited writer precheck blocker.
- The ledger panel shows gate counts, candidate-ready count, and false writer/write flags.
- Configured PAPER capital remains distinct from verified cash/equity.
- Current-evidence writes, portfolio truth writes, live orders, and scale-up remain blocked.

runtime_summary:
- dashboard_blocking_reason: AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED
- precheck_status: BLOCKED_AUDITED_WRITER_DISABLED
- primary_blocker_code: AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED
- audit_gate_pass_count: 6
- audit_gate_blocked_count: 1
- audited_writer_candidate_ready_count: 3
- current_evidence_write_allowed: false
- portfolio_truth_write_allowed: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not implement, enable, or call a current-evidence writer.
- It does not write portfolio truth, LIVE_READY, live config, orders, or scale-up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T12:10:25Z
