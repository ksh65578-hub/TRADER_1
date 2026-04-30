# MVP4_DASHBOARD_STABILITY_SCALEUP_LOCK

context_pack_id: MVP4_DASHBOARD_STABILITY_SCALEUP_LOCK
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD", "SECTION_RISK_SCALE_UP_BLOCKER"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-STABILITY-SCALEUP-LOCK"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["read_only_dashboard_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_stability_scaleup_lock_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_STABILITY_SCALEUP_LOCK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Stability Trends includes explicit scale_up_allowed=false.
- The dashboard schema requires stability_trends.scale_up_allowed=false.
- Dashboard validation blocks stability trends when scale_up_allowed drifts true.
- Launcher dashboards are regenerated under safe local mode without credentials.

known_omissions_by_design:
- no actual long-run runtime evidence is created by this patch
- no live order, credential, exchange account, LIVE_ENABLING behavior, or risk scale-up is used

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T05:58:46Z
