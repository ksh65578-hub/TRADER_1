# MVP4_VALIDATOR_DEPTH_AUDIT_RECHECK

context_pack_id: MVP4_VALIDATOR_DEPTH_AUDIT_RECHECK
task_class: MVP4_VALIDATOR_DEPTH_AUDIT_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_VALIDATOR_DEPTH_AUDIT_RECHECK", "SECTION_SCHEMA_CONTRACTS", "SECTION_AGENTS_VALIDATOR_GROUP_NAVIGATION", "SECTION_AGENTS_IMPLEMENTATION_DEPTH_ENFORCEMENT"]
included_requirement_ids: ["REQ-MVP4-VALIDATOR-DEPTH-AUDIT-RECHECK"]
included_schema_ids: ["trader1.convergence_objective_profile.v1"]
included_validator_ids: ["convergence_objective_profile_validator", "validator_depth_audit_tool"]
included_artifact_ids: ["tools/audit_validator_depth.py", "system/evidence/audit_reports/MVP4_VALIDATOR_DEPTH_AUDIT_RECHECK.audit.json", "system/evidence/contract_gaps/VALIDATOR_REGISTRY_BACKLOG_TRIAGE.contract_gap.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- implemented validators are callable and have no blocking depth gaps
- convergence objective profile is no longer schema-only
- net EV after cost and fee/slippage/drawdown/OOS components are required
- registry groups include implemented safety validators
- future registry validators remain backlog only and cannot be treated as PASS
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live credentials
- no live order API
- no LIVE_ENABLING_PATCH
- registered but unimplemented future validators stay contract_gap/backlog

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. Generated context packs are not authority.
generated_at_utc: 2026-04-29T12:07:43Z
