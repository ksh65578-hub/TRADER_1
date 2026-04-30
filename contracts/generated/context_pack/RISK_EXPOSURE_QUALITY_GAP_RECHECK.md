# RISK_EXPOSURE_QUALITY_GAP_RECHECK

context_pack_id: RISK_EXPOSURE_QUALITY_GAP_RECHECK
task_class: MVP4_RISK_EXPOSURE_QUALITY_GAP_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_RISK_SIZING_EXPOSURE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-RISK-EXPOSURE-QUALITY-GAP-RECHECK"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "read_only_dashboard_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_risk_exposure_quality_gap_recheck_patch_evidence.py", "contracts/generated/context_pack/RISK_EXPOSURE_QUALITY_GAP_RECHECK.md", "system/evidence/audit_reports/MVP4_RISK_EXPOSURE_QUALITY_GAP_RECHECK_20260429.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]

acceptance_checklist:
- Missing paper_exposure_quality_report demotes risk panel to ATTENTION/yellow.
- Missing paper exposure quality next evidence fails closed.
- Paper exposure quality next evidence is rendered for the operator.
- Live and scale-up flags remain false.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T08:17:27Z
