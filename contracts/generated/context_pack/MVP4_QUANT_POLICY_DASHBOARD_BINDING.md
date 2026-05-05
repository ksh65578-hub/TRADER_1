# MVP4_QUANT_POLICY_DASHBOARD_BINDING

context_pack_id: MVP4_QUANT_POLICY_DASHBOARD_BINDING
task_class: MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION
included_section_ids: ["SECTION_DASHBOARD_UX", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-QUANT-POLICY-DASHBOARD-BINDING"]
included_schema_ids: ["trader1.summary.v1", "trader1.read_only_dashboard_shell.v1", "trader1.quantitative_policy_report.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "summary_shell_validator", "read_only_dashboard_validator", "upbit_paper_runtime_cycle_validator", "quantitative_policy_validator", "live_final_guard_validator", "optimizer_no_live_mutation_validator"]
included_artifact_ids: ["contracts/schema/summary.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/summary_writer.py", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/paper/upbit_paper_runtime.py", "trader1/validation/mvp0_validators.py", "tests/dashboard/test_summary_writer.py", "tests/dashboard/test_read_only_dashboard.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "tools/emit_quant_policy_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_QUANT_POLICY_DASHBOARD_BINDING.md", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/IMPLEMENTATION_COVERAGE_MATRIX.md", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/ACCEPTANCE_REPORT.json", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/pytest_report.txt", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/PAPER_RUN_SUMMARY.json", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/LIVE_BLOCK_PROOF.json", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/DASHBOARD_READINESS_SUMMARY.json", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/USER_STATUS_SUMMARY.md", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/TRADER_1_SESSION_REVIEW.md", "system/evidence/session_reviews/MVP4_QUANT_POLICY_DASHBOARD_BINDING/QUANT_POLICY_DASHBOARD_BINDING_REPORT.json"]

acceptance_checklist:
- summary.json carries quantitative_policy_summary as dashboard-only.
- read_only_dashboard_shell carries quantitative_policy_status as display-only.
- Upbit PAPER runtime summary binds a cycle-scoped quantitative policy report id.
- Binance summary remains scaffold-only and does not inherit Upbit readiness.
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false.

known_omissions_by_design:
- No LIVE_READY write.
- No live order path.
- No credential or private API use.
- No open contract gap closure.
