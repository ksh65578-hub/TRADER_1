# MVP4 Persistent Runtime Duration Evidence Guard

context_pack_id: MVP4_PERSISTENT_RUNTIME_DURATION_EVIDENCE_GUARD
task_class: MVP4_RUNTIME_REPRODUCIBILITY_AND_LONG_RUN_EXECUTION_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

## Included Sections
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_RUNTIME_RECOVERY_RTO_ACTIVE
- SECTION_LIVE_FINAL_GUARD

## Requirement
- REQ-MVP4-PERSISTENT-RUNTIME-DURATION-EVIDENCE-GUARD: persistent SHADOW runtime stub duration fields must remain explicit STUB_ESTIMATE_ONLY / NOT_LONG_RUN_EVIDENCE and cannot claim observed wall-clock runtime.

## Acceptance Checklist
- observed_runtime_seconds remains 0 for bounded stub reports.
- estimated_runtime_seconds is derived from completed_cycle_count * heartbeat_interval_seconds.
- mutated OBSERVED_WALL_CLOCK or LONG_RUN_EVIDENCE duration claims block as ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING.
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false.

## Known Omissions
- Actual repeated scheduled PAPER/SHADOW runtime execution is still not provided.
- This context pack is navigation/cache only and is not authority.
