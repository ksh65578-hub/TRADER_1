# FULL_SYSTEM_UI_SAFETY_AUDIT

context_pack_id: FULL_SYSTEM_UI_SAFETY_AUDIT
task_class: MVP4_FULL_SYSTEM_UI_SAFETY_AUDIT
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_DASHBOARD_SHELL", "SECTION_ROOT_LAUNCHER", "SECTION_NAMESPACE_TRUTH", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_RETAINED_ARCHIVE"]
included_requirement_ids: ["REQ-MVP0-LIVE-BLOCKED-MATRIX", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD", "REQ-MVP1-RECONCILIATION-SCAFFOLD", "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.read_only_dashboard_shell.v1", "trader1.root_launcher_report.v1", "trader1.live_preflight_report.v1", "trader1.risk_scaling_decision.v1"]
included_validator_ids: ["authority_integrity_validator", "external_authority_manifest_validator", "registry_validator", "schema_validator", "closed_enum_validator", "common_defs_drift_validator", "patch_result_schema_validator", "coverage_index_validator", "active_schema_extraction_validator", "generated_artifact_dirty_validator", "live_blocked_negative_matrix_validator", "source_bundle_hygiene_validator", "secret_scan_validator", "path_namespace_validator", "truth_hierarchy_validator", "root_launcher_guard_validator", "root_launcher_surface_validator", "runtime_config_validator", "single_writer_order_path_validator", "strategy_direct_order_validator", "readiness_surface_validator", "live_ready_snapshot_writer_validator", "live_final_guard_validator", "upbit_live_review_preflight_validator", "read_only_dashboard_validator", "ledger_durability_validator", "reconciliation_validator", "ledger_reconciliation_validator", "restart_recovery_validator", "emergency_flatten_validator", "operator_action_audit_validator", "operator_control_validator", "upbit_paper_dry_run_validator", "upbit_operational_paper_gate_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "scale_up_eligibility_validator", "risk_scaling_decision_validator", "live_burn_in_feedback_validator", "paper_live_parity_validator", "execution_quality_measurement_validator", "survival_layer_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "contracts/generated/current_implementation_state.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- dashboard is display-only
- live launchers are hard-blocked
- optimizer and convergence cannot create live permission

known_omissions_by_design:
- no real exchange account access
- no credential loading
- no manual order test
- no live burn-in
- no LIVE_ENABLING_PATCH

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T21:59:35Z
