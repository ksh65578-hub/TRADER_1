# MVP4_STABILITY_HISTORY_DISTINCT_SNAPSHOT_GUARD

context_pack_id: MVP4_STABILITY_HISTORY_DISTINCT_SNAPSHOT_GUARD
task_class: MVP4_STABILITY_HISTORY_DISTINCT_SNAPSHOT_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_LONG_RUN_OPERATION
- SECTION_RUNTIME_STABILITY_HISTORY
- SECTION_DASHBOARD_OPERATOR_VISIBILITY
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-STABILITY-HISTORY-DISTINCT-SNAPSHOT-GUARD
included_schema_ids:
- trader1.runtime_stability_history.v1
included_validator_ids:
- runtime_stability_history_validator
- read_only_dashboard_validator
- live_final_guard_validator
acceptance_checklist:
- repeated identical dashboard snapshots cannot produce VALIDATED_HISTORY
- single ATTENTION or ERROR snapshot propagates to history_status
- unsafe SHADOW harness display stays blocked and dashboard writer does not crash
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false
known_omissions_by_design:
- no live-enabling evidence requested or produced
- no external account, API key, or credential access
conflict_resolution_rule: TRADER_1.md wins over generated context pack
