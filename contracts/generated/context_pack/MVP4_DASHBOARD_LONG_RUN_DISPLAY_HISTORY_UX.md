# MVP4_DASHBOARD_LONG_RUN_DISPLAY_HISTORY_UX

context_pack_id: MVP4_DASHBOARD_LONG_RUN_DISPLAY_HISTORY_UX
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-LONG-RUN-DISPLAY-HISTORY-UX"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["read_only_dashboard_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_long_run_display_history_ux_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_LONG_RUN_DISPLAY_HISTORY_UX.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/launcher/root_launcher_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/launcher/root_launcher_report.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Long-run display status says Display History Stable instead of sounding like live-ready validation.
- Display history is explicitly described as display-only and insufficient for actual 24h runtime evidence.
- Runtime evidence boundary tells the operator to use persistent PAPER/SHADOW runtime evidence, not display history alone.
- Sparse or short display history cannot create live readiness, order permission, scorecard promotion, or scale-up.

known_omissions_by_design:
- no actual 24h plus 2880-cycle long-run runtime evidence is created by this patch
- no API keys, credentials, exchange account calls, order-capable endpoints, live orders, live config mutation, or scale-up are used
- ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING remains open

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T06:52:17Z
