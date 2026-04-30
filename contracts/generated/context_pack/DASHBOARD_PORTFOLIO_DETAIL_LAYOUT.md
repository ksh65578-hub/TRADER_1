# DASHBOARD_PORTFOLIO_DETAIL_LAYOUT

context_pack_id: DASHBOARD_PORTFOLIO_DETAIL_LAYOUT
task_class: MVP4_DASHBOARD_PORTFOLIO_DETAIL_LAYOUT
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-PORTFOLIO-DETAIL-LAYOUT"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_portfolio_detail_layout_patch_evidence.py", "contracts/generated/context_pack/DASHBOARD_PORTFOLIO_DETAIL_LAYOUT.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]

acceptance_checklist:
- First screen portfolio shows cash, equity, locked cash, realized PnL, unrealized PnL, total PnL, open positions, entry candidates, and return.
- Held positions and entry candidates are visible in compact first-screen lists.
- Detailed validator/source/status sections remain collapsed below.
- Tables are wrapped to prevent narrow-screen clipping.
- No order buttons, forms, submit controls, live flags, or scale-up permissions are introduced.

coverage_snapshot:
- dashboard_count: 2
- checked_items: 12
- audit_status: PASS
- browser_visual_check: PASS_IN_APP_BROWSER_NARROW_VIEW
- playwright_overflow_check: UNTESTED_PLAYWRIGHT_NOT_AVAILABLE

known_omissions_by_design:
- no live execution
- no credential access
- no exchange real-account call
- no LIVE_READY snapshot write
- no live or active config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T10:09:58Z
