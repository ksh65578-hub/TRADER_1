# DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK

context_pack_id: DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK
task_class: MVP4_DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-RECONCILIATION-OPERATOR-UX-RECHECK"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "reconciliation_validator", "restart_recovery_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "trader1/validation/mvp0_validators.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_reconciliation_operator_ux_recheck_patch_evidence.py", "contracts/generated/context_pack/DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard first screen shows a dedicated Ledger & Reconciliation panel.
- Missing reconciliation/restart evidence is visible as yellow warning, not hidden behind green operation status.
- PASS reconciliation/restart evidence displays green but still shows LIVE_READY_MISSING and all live flags false.
- Reconciliation mismatch displays red BLOCKED and does not create order permission.
- Dashboard validator blocks any reconciliation panel live/order/scale flag drift.

coverage_snapshot:
- default_panel_status: NOT_LOADED
- default_panel_color: yellow
- pass_panel_status: PASS
- pass_panel_color: green
- mismatch_panel_status: BLOCKED
- mismatch_panel_color: red
- live_drift_result: BLOCKED

known_omissions_by_design:
- no live execution
- no credential access
- no exchange real-account call
- no LIVE_READY snapshot write
- no live or active config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T09:30:04Z
