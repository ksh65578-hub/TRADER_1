# MVP4_DASHBOARD_OPERATOR_FOCUS_SIMPLIFICATION

context_pack_id: MVP4_DASHBOARD_OPERATOR_FOCUS_SIMPLIFICATION
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-OPERATOR-FOCUS-SIMPLIFICATION", "REQ-MVP4-DASHBOARD-FIRST-SCREEN-SIMPLIFICATION", "REQ-MVP4-DASHBOARD-VISIBILITY-LAYOUT-FIX"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["read_only_dashboard_validator", "dashboard_visual_layout_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_operator_focus_simplification_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_OPERATOR_FOCUS_SIMPLIFICATION.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard/index.html", "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard/index.html"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- First visible dashboard decision surface answers Run, Portfolio, and Live before technical evidence.
- The decision surface names the three operator questions: running normally, PAPER portfolio, and live orders.
- Portfolio details and open PAPER positions are visible before the detailed evidence drawer.
- Dashboard Data Freshness and Source Artifacts are preserved for audit, but moved below the operator answers.
- Base text size, answer card spacing, and portfolio KPI minimum widths are increased.
- No order controls, live permission, credential access, live config mutation, or scale-up behavior is introduced.

known_omissions_by_design:
- runtime HTML files may be refreshed locally for operator visibility but remain untracked runtime output
- dashboard remains display truth only and cannot become execution truth
- unresolved MVP-4 evidence gaps remain open and live-blocking

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-05T02:49:07Z
