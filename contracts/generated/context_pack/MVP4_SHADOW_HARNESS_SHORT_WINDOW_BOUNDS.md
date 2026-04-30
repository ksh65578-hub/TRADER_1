# MVP4_SHADOW_HARNESS_SHORT_WINDOW_BOUNDS

context_pack_id: MVP4_SHADOW_HARNESS_SHORT_WINDOW_BOUNDS
task_class: MVP4_LONG_RUN_PAPER_SHADOW_EVIDENCE_ORCHESTRATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_LONG_RUN_OPERATION
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-SHADOW-HARNESS-SHORT-WINDOW-BOUNDS
included_schema_ids:
- trader1.shadow_observation_actual_runtime_harness_report.v1
included_validator_ids:
- shadow_observation_actual_runtime_harness_validator
- paper_shadow_evidence_accumulation_validator
- live_final_guard_validator

## Acceptance Checklist

- Short-window harness cycle count, heartbeat count, observation fan-out, and measured runtime are bounded.
- Short-window harness cannot satisfy long-run duration or cycle thresholds by lowering threshold inputs.
- Harness output remains display-only, not optimizer ranking input, not LIVE_READY evidence, and not scale-up evidence.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

## Known Omissions By Design

- No real exchange credential, account, or live order path was used.
- True long-run PAPER/SHADOW evidence remains blocked until an actual non-live long-window run produces validated duration, cycle, heartbeat, recovery, and profitability evidence.

conflict_resolution_rule: TRADER_1.md wins over generated context pack.
