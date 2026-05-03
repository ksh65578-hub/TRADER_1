# MVP4_DASHBOARD_AUDITED_CURRENT_EVIDENCE_SOURCE_FRESHNESS

context_pack_id: MVP4_DASHBOARD_AUDITED_CURRENT_EVIDENCE_SOURCE_FRESHNESS
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-AUDITED-CURRENT-EVIDENCE-SOURCE-FRESHNESS"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_audited_current_evidence_source_freshness_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_AUDITED_CURRENT_EVIDENCE_SOURCE_FRESHNESS.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Stale audited_current_evidence_snapshot keeps portfolio and positions UNVERIFIED.
- The audited current-evidence source artifact displays STALE when generated_at_utc exceeds dashboard TTL.
- Verified audited PAPER portfolio display still requires validated writer/current/portfolio evidence and live blockers.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live execution
- no credential or private account access
- no LIVE_READY snapshot write
- no live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-03T11:45:33Z
