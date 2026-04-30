# MVP4_EXECUTION_FAILURE_SLIPPAGE_TAXONOMY_VALIDATORS

context_pack_id: MVP4_EXECUTION_FAILURE_SLIPPAGE_TAXONOMY_VALIDATORS
task_class: MVP4_REGISTERED_VALIDATOR_BACKLOG_TRIAGE_CONTINUE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_EXECUTION_FEEDBACK", "SECTION_CONVERGENCE_MEMORY", "SECTION_OPTIMIZER_ROBUSTNESS", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-EXECUTION-FAILURE-SLIPPAGE-TAXONOMY-VALIDATORS"]
included_schema_ids: ["trader1.optimizer_feedback_report.v1", "trader1.failure_analysis_report.v1"]
included_validator_ids: ["realized_slippage_validator", "order_failure_taxonomy_validator", "execution_feedback_loop_validator", "failure_analysis_validator"]
included_artifact_ids: ["trader1/validation/mvp0_validators.py", "tests/validators/test_execution_failure_backlog_validators.py", "system/evidence/contract_gaps/VALIDATOR_REGISTRY_BACKLOG_TRIAGE.contract_gap.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- realized slippage deviation is positive realized-minus-expected cost drift only
- divergent slippage blocks ranking instead of improving optimizer status
- known execution/slippage failures cannot remain UNKNOWN_ROOT_CAUSE
- execution failure taxonomy requires explicit blocker evidence and promotion block
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live exchange call
- no live order submission
- no LIVE_ENABLING_PATCH
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This pack is a navigation/cache artifact only.

generated_at_utc: 2026-04-29T13:07:18Z
