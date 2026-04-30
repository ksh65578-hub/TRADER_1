# SHADOW_OBSERVATION_ACTUAL_RUNTIME_HARNESS

context_pack_id: SHADOW_OBSERVATION_ACTUAL_RUNTIME_HARNESS
task_class: MVP4_SHADOW_OBSERVATION_ACTUAL_LONG_RUN_EXECUTION_HARNESS
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: SECTION_PAPER_SHADOW_EVIDENCE, SECTION_LIVE_FINAL_GUARD
included_requirement_ids: REQ-MVP4-SHADOW-OBSERVATION-ACTUAL-RUNTIME-HARNESS
included_schema_ids: trader1.shadow_observation_actual_runtime_harness_report.v1
included_validator_ids: shadow_observation_actual_runtime_harness_validator, live_final_guard_validator
conflict_resolution_rule: TRADER_1.md wins over generated context.

Acceptance checklist:
- non-live PAPER/SHADOW harness may run short-window local checks only
- no credential, no exchange account, no live API, no order adapter
- short-window harness output is not long-run evidence
- optimizer ranking, promotion, LIVE_READY, and scale-up stay blocked
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false
