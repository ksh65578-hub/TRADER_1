# MVP4_DASHBOARD_POSITION_DETAIL_TRUTH_GUARD

context_pack_id: MVP4_DASHBOARD_POSITION_DETAIL_TRUTH_GUARD
task_class: MVP4_DASHBOARD_POSITION_DETAIL_TRUTH_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-POSITION-DETAIL-TRUTH-GUARD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.patch_result.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_position_detail_truth_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_POSITION_DETAIL_TRUTH_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard position rows must preserve verified PAPER fill detail fields.
- average_entry_price must display as Avg Price instead of UNKNOWN.
- Mark price, market value, cost basis, and unrealized PnL must be operator-visible.
- Dashboard remains display truth only and cannot create live, order, or scale-up permission.

audit_status: PASS

known_omissions_by_design:
- no live execution
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T18:12:54Z
