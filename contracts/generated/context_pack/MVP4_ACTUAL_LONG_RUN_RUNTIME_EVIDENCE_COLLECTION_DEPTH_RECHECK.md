# MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK

context_pack_id: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK
task_class: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK", "REQ-MVP4-UPBIT-PAPER-RUNTIME-EVIDENCE-COLLECTION-PROFILE", "REQ-MVP4-DASHBOARD-UPBIT-PAPER-RUNTIME-EVIDENCE-PROFILE-BINDING"]
included_schema_ids: ["trader1.upbit_paper_runtime_evidence_collection_profile_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_sample_history_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "paper_ledger_rollup_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "tools/run_upbit_paper_runtime_evidence_collection_profile.py", "trader1/dashboard/read_only_dashboard.py", "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py", "tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py", "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py", "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py", "tests/contract/test_completed_recheck_route_depth_guard.py", "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py", "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py", "tests/contract/test_open_contract_gap_implementation_priority_recheck.py", "tests/contract/test_patch_result_runtime_schema_validation.py", "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py", "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_post_repair_reconciliation_required_recheck.py", "tests/contract/test_post_rerun_current_evidence_write_blocked_implementation_depth_recheck.py", "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py", "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_implementation_depth_recheck.py", "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py", "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py", "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py", "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py", "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py", "tests/contract/test_stale_loop_regeneration_required_recheck.py", "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py", "system/evidence/runtime_checks/MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json", "tools/emit_actual_long_run_runtime_evidence_collection_depth_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_COLLECTION_DEPTH_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Bounded PAPER runtime evidence profile exposes long_run_collection_depth.
- Collection depth remains BLOCKED_FOR_LONG_RUN_COLLECTION_DEPTH and shows missing SHADOW runtime depth.
- Span and cycle deficits are hash-covered and projected to dashboard display truth.
- Dashboard validation blocks hidden missing SHADOW depth or false bounded-profile long-run claims.
- ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY remains OPEN and live-affecting.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_snapshot:
- audit_status: PASS
- profile_status: PASS
- accepted_cycle_sample_count: 2
- missing_span_seconds: 86400
- missing_cycle_count: 2878
- missing_runtime_modes: ["SHADOW"]

known_omissions_by_design:
- this patch does not create actual 24h PAPER/SHADOW long-run evidence
- this patch does not close ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY
- this patch does not use credentials, call private endpoints, place live orders, mutate live config, or scale up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-04T23:23:20Z
