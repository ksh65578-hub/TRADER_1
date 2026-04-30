# MVP4_STABILITY_HISTORY_MIN_SPAN_GUARD

context_pack_id: MVP4_STABILITY_HISTORY_MIN_SPAN_GUARD
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_ORCHESTRATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: SECTION_RUNTIME_RECOVERY_RTO_ACTIVE, SECTION_DASHBOARD_SHELL, SECTION_LIVE_FINAL_GUARD
included_requirement_ids: REQ-MVP4-STABILITY-HISTORY-MIN-SPAN-GUARD
included_schema_ids: trader1.runtime_stability_history.v1, trader1.read_only_dashboard_shell.v1
included_validator_ids: runtime_stability_history_validator, read_only_dashboard_validator, runtime_schema_instance_validator, live_final_guard_validator

## Delta

Runtime stability history now requires a minimum observed sample span before it can report VALIDATED_HISTORY. Dashboard long-run status only shows VALIDATED_STABLE when the stability history span is SPAN_VALIDATED and remains display-only/live-blocked.

## Acceptance Checklist

- Short-span distinct dashboard snapshots remain INSUFFICIENT_HISTORY.
- Minimum-span distinct dashboard snapshots can validate history.
- Dashboard keeps short-span history in RUNNING_NOW/CURRENT_SNAPSHOT_ONLY.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
