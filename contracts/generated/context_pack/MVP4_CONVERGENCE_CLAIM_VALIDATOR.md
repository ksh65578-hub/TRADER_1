# MVP4_CONVERGENCE_CLAIM_VALIDATOR

context_pack_id: MVP4_CONVERGENCE_CLAIM_VALIDATOR
task_class: MVP4_REGISTERED_VALIDATOR_BACKLOG_TRIAGE_CONTINUE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_PROFIT_CONVERGENCE_MVP3
- SECTION_CONVERGENCE_GUARDRAIL
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-CONVERGENCE-CLAIM-VALIDATOR
included_schema_ids:
- trader1.convergence_assessment_report.v1
included_validator_ids:
- convergence_claim_validator
acceptance_checklist:
- convergence claim cannot create live, writer input, order, or scale-up permission
- improving claims require PASS dependencies, fresh evidence, NO_DRIFT, no blockers, and no forbidden profitability wording
- dashboard/operator text must remain analysis-only, not LIVE_READY, live orders blocked, and no profit guarantee
known_omissions_by_design:
- no LIVE_ENABLING_PATCH
- no live exchange/API/credential evidence
conflict_resolution_rule: TRADER_1.md wins over generated cache.
