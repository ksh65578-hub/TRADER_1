# MVP4_DASHBOARD_VISIBILITY_LAYOUT_FIX

context_pack_id: MVP4_DASHBOARD_VISIBILITY_LAYOUT_FIX
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-VISIBILITY-LAYOUT-FIX", "REQ-MVP4-DASHBOARD-VISUAL-LAYOUT-QA", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["read_only_dashboard_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_visibility_layout_fix_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_VISIBILITY_LAYOUT_FIX.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard freshness header summarizes source artifacts with bounded Total/PASS/Attention chips.
- Long ARTIFACT=STATUS source traces remain available in the Source Artifacts table, not in the first-screen header.
- Visual layout contract blocks cramped fixed-column regressions.
- Read-only safety text and live/scale flags remain false.

known_omissions_by_design:
- no live order, credential, account API, live config mutation, or scale-up path is introduced
- runtime index.html files may be refreshed locally for operator visibility but must not be staged as source changes
- unresolved MVP-4 runtime evidence gaps remain open

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-03T23:06:11Z
