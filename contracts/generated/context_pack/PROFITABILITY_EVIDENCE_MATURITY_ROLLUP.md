# PROFITABILITY_EVIDENCE_MATURITY_ROLLUP

context_pack_id: PROFITABILITY_EVIDENCE_MATURITY_ROLLUP
task_class: VALIDATOR_PATCH
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_STRATEGY_PROFITABILITY_EVIDENCE
- SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR
included_schema_ids:
- trader1.profitability_evidence_maturity_rollup.v1
included_validator_ids:
- profitability_evidence_maturity_rollup_validator
- profitability_optimizer_evidence_gap_validator
conflict_resolution_rule: TRADER_1.md remains highest authority; this context pack is only a read cache.

## Delta

Adds a schema-backed profitability evidence maturity rollup for ten required profitability, strategy, optimizer, convergence, and dashboard components. The rollup is display and validation evidence only. It cannot create LIVE_READY, live permission, live config mutation, or scale-up permission.

## Acceptance Checklist

- all ten profitability maturity components are present
- component validator states are not FAIL, UNTESTED, STALE, or TIMEOUT
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- next_operator_action explicitly directs PAPER/SHADOW evidence collection and states live remains blocked
