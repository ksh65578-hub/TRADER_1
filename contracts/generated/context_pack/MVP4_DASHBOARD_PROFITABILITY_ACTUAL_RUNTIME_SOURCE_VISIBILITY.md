# MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY

context_pack_id: MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-PROFITABILITY-ACTUAL-RUNTIME-SOURCE-VISIBILITY"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html", "tools/emit_dashboard_profitability_actual_runtime_source_visibility_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard profitability maturity exposes actual non-live runtime source status and source count.
- Long-run evidence cannot display eligible unless a validated non-live runtime source exists.
- Dashboard schema requires the runtime source fields so regenerated PAPER dashboards cannot silently omit the blocker.
- Narrow dashboard layouts wrap long status tokens and evidence details instead of clipping them horizontally.
- UPBIT and BINANCE PAPER dashboard artifacts are regenerated through the safe launcher and remain live-blocked.

known_omissions_by_design:
- no actual 24h PAPER/SHADOW long-run runtime evidence is created
- no official API verification, account snapshot, credential, live order, live config mutation, or scale-up is used
- ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING remains open

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T07:28:09Z
