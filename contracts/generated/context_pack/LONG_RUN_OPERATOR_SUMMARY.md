# LONG_RUN_OPERATOR_SUMMARY

context_pack_id: LONG_RUN_OPERATOR_SUMMARY
task_class: MVP4_LONG_RUN_OPERATOR_SUMMARY_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_RUNTIME_STABILITY", "SECTION_OPERATOR_VISIBILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-LONG-RUN-OPERATOR-SUMMARY-HARDENING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.runtime_stability_history.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "runtime_stability_history_validator", "runtime_resource_pressure_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_long_run_operator_summary_hardening_patch_evidence.py", "contracts/generated/context_pack/LONG_RUN_OPERATOR_SUMMARY.md", "system/evidence/audit_reports/MVP4_LONG_RUN_OPERATOR_SUMMARY_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- first screen shows whether the program is running normally now
- normal operation uses blue or green, warning uses yellow, error uses red
- long-run VALIDATED_STABLE requires at least two clean stability history samples
- stale, missing, or degraded history cannot be displayed as stable
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live exchange data, account data, credential, live order, or LIVE_READY snapshot is consumed
- long-run summary is display-only and cannot become execution truth
- running-now status is not a live readiness claim

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T02:53:34Z
