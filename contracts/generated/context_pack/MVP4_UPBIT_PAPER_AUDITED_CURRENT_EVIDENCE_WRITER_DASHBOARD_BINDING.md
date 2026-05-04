# MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING

context_pack_id: MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING
task_class: MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING", "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1", "trader1.upbit_paper_audited_current_evidence_snapshot.v1", "trader1.paper_portfolio_snapshot.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_repaired_current_evidence_audited_writer_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/validation/mvp0_validators.py", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py", "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py", "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py", "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py", "tests/contract/test_patch_result_runtime_schema_validation.py", "tests/contract/test_post_repair_reconciliation_required_recheck.py", "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py", "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py", "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py", "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py", "tests/contract/test_stale_loop_regeneration_required_recheck.py", "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py", "tools/emit_upbit_paper_audited_current_evidence_writer_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_rollup_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repaired_current_evidence_audited_writer_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/current_evidence/audited_current_evidence_snapshot.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/portfolio/paper_portfolio_snapshot.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The audited current-evidence writer validator compares portfolio truth to the source ledger snapshot, not a stale fixed cash sample.
- The safe launcher loads the audited writer report, audited current-evidence snapshot, and audited paper portfolio snapshot.
- The dashboard portfolio card displays VERIFIED audited PAPER truth from audited_current_evidence_snapshot.json.
- The position panel binds paper_portfolio_snapshot.json and preserves the audited open-position count.
- Source artifacts for writer, current evidence, and audited portfolio all show PASS.
- Live order readiness, live order permission, trading permission, and scale-up all remain false.

runtime_summary:
- writer_status: PASS_AUDITED_CURRENT_EVIDENCE_WRITTEN
- writer_validation_status: PASS
- writer_verified_for_display: True
- portfolio_status: VERIFIED
- portfolio_source: audited_current_evidence_snapshot.json
- source_cash_krw: 840420.25
- source_equity_krw: 999920.2499999999999999999997
- open_position_count: 1
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not write repo-local system/runtime monitor output.
- It does not create LIVE_READY, live config, live orders, private API calls, credentials, long-run evidence, or scale-up.
- It does not close unrelated open contract gaps such as profitability maturity or long-run runtime evidence.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-04T04:34:46Z
