# MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY

context_pack_id: MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY
task_class: MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-TRIAL-DURATION-POLICY", "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-RUN-PREFLIGHT", "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-INTAKE-AUDIT", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.residual_operator_evidence_trial_duration_policy_report.v1", "trader1.residual_operator_evidence_run_preflight_report.v1", "trader1.residual_operator_evidence_intake_audit_report.v1"]
included_validator_ids: ["runtime_schema_instance_validator", "schema_validator", "registry_validator", "paper_shadow_evidence_accumulation_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/patch_result.schema.json", "contracts/schema/residual_operator_evidence_trial_duration_policy_report.schema.json", "trader1/reports/residual_operator_evidence_trial_duration_policy.py", "tests/contract/test_residual_operator_evidence_trial_duration_policy.py", "tools/emit_residual_operator_evidence_trial_duration_policy_patch_evidence.py", "contracts/generated/context_pack/MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.md", "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py", "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py", "tests/contract/test_completed_recheck_route_depth_guard.py", "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py", "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py", "tests/contract/test_open_contract_gap_implementation_priority_recheck.py", "tests/contract/test_patch_result_runtime_schema_validation.py", "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py", "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_post_repair_reconciliation_required_recheck.py", "tests/contract/test_post_rerun_current_evidence_write_blocked_implementation_depth_recheck.py", "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py", "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py", "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_implementation_depth_recheck.py", "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py", "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py", "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py", "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py", "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py", "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py", "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py", "tests/contract/test_stale_loop_regeneration_required_recheck.py", "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py", "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.report.json", "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.report.json", "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.report.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The operator-facing next run is lowered to 24h / 8640 ticks.
- The trial profile remains non-live, credential-free, and not eligible for MVP-5/live readiness evidence.
- The formal MVP-5 review path remains an adaptive evidence-quality gate and is not replaced by the trial.
- No command is executed, no runtime output is staged, and no current evidence write or gap closure is allowed.
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false.

known_omissions_by_design:
- this patch does not change final live readiness evidence requirements
- this patch does not run the 24h trial
- this patch does not close long-run or PAPER/SHADOW evidence gaps

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-05T11:03:44Z
