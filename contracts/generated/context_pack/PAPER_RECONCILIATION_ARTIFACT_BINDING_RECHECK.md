# PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK

context_pack_id: PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK
task_class: MVP4_PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_RUNTIME_ARTIFACT_BINDING", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PAPER-RECONCILIATION-ARTIFACT-BINDING-RECHECK"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "reconciliation_validator", "restart_recovery_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/boot/safe_launcher.py", "tests/runtime/test_safe_launcher.py", "tools/emit_paper_reconciliation_artifact_binding_recheck_patch_evidence.py", "contracts/generated/context_pack/PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/reconciliation_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/restart_recovery_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/reconciliation_report.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Launcher dashboard reads session-scoped reconciliation_report.json when present.
- UPBIT PAPER dashboard reads session-scoped restart_recovery_report.json when present.
- UPBIT PAPER clean reconciliation/restart evidence appears green, but still shows LIVE_READY_MISSING.
- BINANCE PAPER does not fake restart recovery; missing restart evidence remains yellow RECONCILE_REQUIRED.
- Cross-session reconciliation artifacts display invalid red instead of being silently mixed.
- All live/order/scale flags remain false.

coverage_snapshot:
- upbit_reconciliation_status: PASS
- upbit_reconciliation_color: green
- binance_reconciliation_status: RECONCILE_REQUIRED
- binance_reconciliation_color: yellow
- binance_restart_recovery_status: NOT_LOADED

known_omissions_by_design:
- no live execution
- no credential access
- no exchange real-account call
- no LIVE_READY snapshot write
- no live or active config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T09:41:21Z
