# MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY

context_pack_id: MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-LONG-RUN-EVIDENCE-REQUIREMENTS-VISIBILITY"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["read_only_dashboard_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_long_run_evidence_requirements_visibility_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Runtime Evidence Boundary exposes a fixed eight-item long-run evidence checklist.
- Checklist separates loaded source artifacts from actual long-run duration, cycle, and evidence-window proof.
- Checklist entries remain display-only and cannot set live_order_ready, live_order_allowed, can_live_trade, or scale_up_allowed.
- Validator blocks missing checklist entries, reordered checklist entries, hidden live-review blockers, and false PASS on actual long-run proof.
- Actual launcher dashboards are regenerated under safe local mode without credentials.

known_omissions_by_design:
- no actual long-run runtime evidence is created by this patch
- no API keys, credentials, exchange account calls, or order-capable endpoints are used
- no LIVE_READY, live order permission, live config mutation, optimizer promotion, or scale-up is enabled

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T05:34:08Z
