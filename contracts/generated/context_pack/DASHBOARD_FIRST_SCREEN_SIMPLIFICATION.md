# DASHBOARD_FIRST_SCREEN_SIMPLIFICATION

context_pack_id: DASHBOARD_FIRST_SCREEN_SIMPLIFICATION
task_class: MVP4_DASHBOARD_FIRST_SCREEN_SIMPLIFICATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-FIRST-SCREEN-SIMPLIFICATION"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_first_screen_simplification_patch_evidence.py", "contracts/generated/context_pack/DASHBOARD_FIRST_SCREEN_SIMPLIFICATION.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- First screen shows only the key operator questions first: portfolio, system status, live readiness.
- Detailed strategy, risk, convergence, source, and validator sections remain available but collapsed below.
- No order buttons, forms, or submit controls are introduced.
- LIVE_READY and live_order_allowed remain separated and false.
- Existing detailed safety text remains present for audit and review.

coverage_snapshot:
- dashboard_count: 2
- checked_items: 5
- audit_status: PASS

known_omissions_by_design:
- no live execution
- no credential access
- no exchange real-account call
- no LIVE_READY snapshot write
- no live or active config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T09:53:31Z
