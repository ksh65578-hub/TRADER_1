# DASHBOARD_SHADOW_HARNESS_STATUS_BINDING

context_pack_id: DASHBOARD_SHADOW_HARNESS_STATUS_BINDING
task_class: MVP4_DASHBOARD_SHADOW_HARNESS_STATUS_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
included_section_ids:
- SECTION_DASHBOARD_OPERATOR_VISIBILITY
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-DASHBOARD-SHADOW-HARNESS-STATUS-BINDING
included_schema_ids:
- trader1.read_only_dashboard_shell.v1
- trader1.shadow_observation_actual_runtime_harness_report.v1
included_validator_ids:
- read_only_dashboard_validator
- shadow_observation_actual_runtime_harness_validator
- runtime_schema_instance_validator
- live_final_guard_validator
acceptance_checklist:
- Dashboard shows the short-window PAPER/SHADOW harness only as display truth.
- Harness output cannot become execution truth, optimizer ranking input, LIVE_READY evidence, live permission, or scale-up permission.
- Runtime dashboard artifacts regenerate with shadow_runtime_harness_status present.
- Stale or unsafe harness reports render as WARNING or ERROR, never as live-ready.
known_omissions_by_design:
- No live exchange access.
- No credential loading.
- No long-run evidence claim.
- No optimizer promotion or active config mutation.
conflict_resolution_rule: TRADER_1.md overrides this generated cache.
