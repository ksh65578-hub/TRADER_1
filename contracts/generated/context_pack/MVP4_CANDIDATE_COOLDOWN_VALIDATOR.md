# MVP4_CANDIDATE_COOLDOWN_VALIDATOR

context_pack_id: MVP4_CANDIDATE_COOLDOWN_VALIDATOR
task_class: MVP4_REGISTERED_VALIDATOR_BACKLOG_TRIAGE_CONTINUE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_CANDIDATE_COOLDOWN
- SECTION_EXPLORATION_EXPLOITATION_POLICY
- SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-CANDIDATE-COOLDOWN-VALIDATOR
included_schema_ids:
- trader1.exploration_exploitation_policy.v1
included_validator_ids:
- candidate_cooldown_validator
- exploration_exploitation_policy_validator
acceptance_checklist:
- cooldown > 0 blocks PAPER ranking review and limited exploitation transition
- COOLDOWN blocker remains operator-visible while cooldown is active
- stale COOLDOWN blocker fails when cooldown_cycles_remaining is zero
- blocked cooldown cannot expose PASS status, live permission, order permission, or scale-up permission
known_omissions_by_design:
- no LIVE_ENABLING_PATCH
- no live exchange/API/credential evidence
- no optimizer winner or paper winner can become live config
conflict_resolution_rule: TRADER_1.md wins over generated cache.
