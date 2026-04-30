# MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY

context_pack_id: MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY
task_class: MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD", "SECTION_DASHBOARD_OPERATOR_UX"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY"]
included_schema_ids: ["trader1.upbit_paper_persistent_loop_report.v1", "trader1.upbit_paper_runtime_recovery_guard_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_recovery_guard_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/common.defs.schema.json", "contracts/schema/upbit_paper_persistent_loop_report.schema.json", "contracts/schema/upbit_paper_runtime_recovery_guard_report.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "trader1/runtime/paper/upbit_paper_persistent_loop.py", "trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_upbit_paper_long_run_evidence_boundary_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY.md"]

acceptance_checklist:
- bounded Upbit PAPER loops expose runtime_evidence_role=BOUNDED_PAPER_LOOP_NOT_LONG_RUN_EVIDENCE
- PAPER recovery guard exposes runtime_evidence_role=PAPER_RECOVERY_GUARD_ONLY_NOT_LONG_RUN_EVIDENCE
- false long-run eligibility is blocked by runtime and dashboard validators
- dashboard shows the long-run blocker while keeping recovery resume status separate from live readiness
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no long-run evidence is created
- no private exchange account, credential, order-capable endpoint, live order, or live-enabling patch is used
- MVP-5 remains blocked by external live-review evidence

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T23:25:58Z
