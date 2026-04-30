# MVP4 Shadow Harness Negative Runtime Measurement Guard

context_pack_id: MVP4_SHADOW_HARNESS_NEGATIVE_RUNTIME_MEASUREMENT_GUARD
task_class: MVP4_RUNTIME_REPRODUCIBILITY_AND_LONG_RUN_EXECUTION_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_RUNTIME_RECOVERY_RTO_ACTIVE
- SECTION_DASHBOARD_SHELL
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-SHADOW-HARNESS-NEGATIVE-RUNTIME-MEASUREMENT-GUARD
- REQ-MVP4-SHADOW-OBSERVATION-ACTUAL-RUNTIME-HARNESS
- REQ-MVP4-DASHBOARD-SHADOW-HARNESS-STATUS-BINDING

## Delta

The short-window PAPER/SHADOW harness now treats negative measured runtime as DATA_QUALITY_INSUFFICIENT. The dashboard no longer hides that source defect by clamping it into a normal-looking zero duration; it renders the harness status as BLOCKED/ERROR display truth while keeping live_order_ready=false, live_order_allowed=false, can_live_trade=false, and scale_up_allowed=false.

## Acceptance Checklist

- Negative measured_runtime_seconds is BLOCKED by validate_shadow_observation_actual_runtime_harness_report.
- Dashboard shadow_runtime_harness_status shows BLOCKED, ERROR, red, and DATA_QUALITY_INSUFFICIENT for negative source measurements.
- Full unittest regression and runtime schema validators pass.
- This context pack is not authority and cannot create live permission.
