# MVP4_PROFIT_CONVERGENCE_CYCLE_VALIDATOR

context_pack_id: MVP4_PROFIT_CONVERGENCE_CYCLE_VALIDATOR
task_class: MVP4_REGISTERED_VALIDATOR_BACKLOG_TRIAGE_CONTINUE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_PROFIT_CONVERGENCE_MVP3
- SECTION_VALIDATOR_IMPLEMENTATION
included_requirement_ids:
- REQ-MVP4-PROFIT-CONVERGENCE-CYCLE-VALIDATOR
included_schema_ids:
- trader1.profit_convergence_cycle_report.v1
included_validator_ids:
- profit_convergence_cycle_validator
included_artifact_ids:
- contracts/schema/profit_convergence_cycle_report.schema.json
- trader1/validation/mvp0_validators.py
- tests/validators/test_profit_convergence_cycle_validator.py
acceptance_checklist:
- profit convergence cycle uses NET_EV_AFTER_COST rather than raw PnL
- UNTESTED dependencies cannot create improvement claim or ranking
- model drift blocks improvement claim and paper ranking
- live, order, writer, and scale-up flags remain false
known_omissions_by_design:
- no live execution, no credentials, no LIVE_ENABLING_PATCH
conflict_resolution_rule: TRADER_1.md wins over this generated read cache.
