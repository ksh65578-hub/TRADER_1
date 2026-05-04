# MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK

context_pack_id: MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK
task_class: MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK", "REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK", "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-IMPLEMENTATION-DEPTH-RECHECK", "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.contract_gap.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1", "trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_post_repair_reconciliation_validator", "upbit_paper_repair_operator_queue_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py", "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py", "tests/contract/test_completed_recheck_route_depth_guard.py", "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py", "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py", "tests/contract/test_open_contract_gap_implementation_priority_recheck.py", "tests/contract/test_patch_result_runtime_schema_validation.py", "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py", "tests/contract/test_post_repair_reconciliation_required_recheck.py", "tests/contract/test_post_rerun_current_evidence_write_blocked_implementation_depth_recheck.py", "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py", "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py", "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py", "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py", "tests/contract/test_stale_loop_regeneration_required_recheck.py", "tools/emit_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.md", "system/evidence/audit_reports/MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_IMPLEMENTATION_DEPTH_RECHECK.json", "system/evidence/contract_gaps/REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED.contract_gap.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_repair_reconciliation_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repair_operator_queue_report.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Confirm the hash-mismatch repair candidate remains BLOCKED.
- Confirm the missing source expected rollup artifact is still not fabricated.
- Confirm repair candidate and operator queue remain review-only and operator-action-required.
- Confirm candidate_current_evidence_usable_count remains 0.
- Keep REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED and BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION open.
- Route to MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_IMPLEMENTATION_DEPTH_RECHECK.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, and scale_up_allowed=false.

depth_snapshot:
- status: PASS_DEPTH_5_REPAIR_CANDIDATE_HASH_MISMATCH_LIVE_BLOCKING
- post_repair_status: BLOCKED
- hash_reconciliation_status: SOURCE_EXPECTED_ROLLUP_ARTIFACT_MISSING
- source_loop_expected_rollup_artifact_load_status: MISSING
- repair_candidate_count: 1
- hash_mismatch_count: 1
- operator_queue_status: BLOCKED
- candidate_current_evidence_usable_count: 0

known_omissions_by_design:
- Does not resolve hash mismatch.
- Does not write current evidence.
- Does not mutate live config.
- Does not call exchange/account/private/live APIs.
- Does not permit live orders or scale-up.
