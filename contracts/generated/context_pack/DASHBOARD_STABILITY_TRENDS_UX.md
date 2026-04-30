# DASHBOARD_STABILITY_TRENDS_UX

context_pack_id: DASHBOARD_STABILITY_TRENDS_UX
task_class: MVP4_DASHBOARD_STABILITY_TRENDS_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_HEARTBEAT", "SECTION_LIVE_FINAL_GUARD", "SECTION_OPERATOR_VISIBILITY"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-HEARTBEAT", "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.heartbeat.v1", "trader1.summary.v1"]
included_validator_ids: ["schema_validator", "read_only_dashboard_validator", "summary_shell_validator", "heartbeat_validator", "root_launcher_surface_validator", "live_blocked_scaffold_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- dashboard exposes stability checks for heartbeat age, source freshness, resources, event latency, queue backlog, and rate-limit pressure
- stable status requires PASS metrics and normal operation status
- warning status uses yellow and error status uses red
- stability trends are current-snapshot-only unless a validated history artifact exists
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no long-run trend claim is made without validated history
- no live order path is enabled
- no exchange account call, credential load, or live burn-in is performed
- dashboard remains display truth only, not execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T23:24:12Z
