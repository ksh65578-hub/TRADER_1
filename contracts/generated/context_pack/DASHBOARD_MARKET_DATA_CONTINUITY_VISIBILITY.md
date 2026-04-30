# DASHBOARD_MARKET_DATA_CONTINUITY_VISIBILITY

context_pack_id: DASHBOARD_MARKET_DATA_CONTINUITY_VISIBILITY
task_class: MVP4_DASHBOARD_MARKET_DATA_CONTINUITY_VISIBILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-MARKET-DATA-CONTINUITY-VISIBILITY"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_public_rest_continuity_history.v1"]
included_validator_ids: ["read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_public_rest_continuity_history_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "trader1/runtime/paper/upbit_public_rest_continuity_history.py", "tests/dashboard/test_read_only_dashboard.py", "tests/integration/test_upbit_public_rest_continuity_history.py", "tests/validators/test_runtime_stability_history_validator.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "contracts/generated/context_pack/DASHBOARD_MARKET_DATA_CONTINUITY_VISIBILITY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- first screen shows whether market data continuity is loaded, blocked, stale, invalid, or PASS
- source artifact is rest_continuity_history.json and remains dashboard display truth only
- PAPER continuity history cannot imply live readiness, promotion eligibility, long-run evidence, or scale-up
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no private exchange call
- no live evidence collection
- no LIVE_READY snapshot write
- no live config mutation

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T12:45:49Z
