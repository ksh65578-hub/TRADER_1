# MVP4 Rolling Window Default Validator Context Pack

context_pack_id: MVP4_ROLLING_WINDOW_DEFAULT_VALIDATOR
task_class: VALIDATOR_PATCH
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: SECTION_ROLLING_WINDOW_DEFAULTS, SECTION_OOS_ROBUSTNESS, SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL, SECTION_LIVE_FINAL_GUARD
included_requirement_ids: REQ-MVP4-ROLLING-WINDOW-DEFAULT-VALIDATOR
included_schema_ids: trader1.overfit_diagnostic_report.v1
included_validator_ids: rolling_window_default_validator, ranking_stability_validator, overfit_diagnostic_validator, optimizer_guardrail_validator, convergence_assessment_validator
included_artifact_ids: tests/validators/test_rolling_window_default_validator.py; tests/validators/fixtures/rolling_window_default_*.json

Acceptance checklist:
- rolling_window_default_validator is implemented in trader1.validation.mvp0_validators.
- Short-window, low train/OOS/walk-forward count, stale status, and insufficient source evidence fixtures fail closed.
- The validator is included in optimizer/convergence guardrail execution and convergence assessment dependency checks.
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false.

Known omissions by design:
- This patch does not create LIVE_READY evidence, does not use credentials, and does not mutate live config.

Conflict resolution rule:
- TRADER_1.md remains the highest design authority; this context pack is only a read cache.
