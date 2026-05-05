# MVP4_DECISION_ARBITER_CONFLICT_PRIORITY

context_pack_id: MVP4_DECISION_ARBITER_CONFLICT_PRIORITY
task_class: MVP4_DECISION_ARBITER_CONFLICT_PRIORITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_STRATEGY_ENTRY_EXIT_NO_TRADE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DECISION-ARBITER-CONFLICT-PRIORITY"]
included_schema_ids: ["trader1.final_decision.v1", "trader1.common_defs.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_paper_dry_run_validator", "upbit_operational_paper_gate_validator", "upbit_paper_runtime_cycle_validator", "runtime_schema_instance_validator", "optimizer_no_live_mutation_validator", "profitability_optimizer_evidence_gap_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator"]
included_artifact_ids: ["trader1/core/decision/decision_arbiter.py", "trader1/adapters/upbit/paper_broker.py", "trader1/runtime/paper/operational_cycle.py", "trader1/runtime/paper/upbit_paper_runtime.py", "tests/contract/test_decision_arbiter_conflict_priority.py", "tools/emit_decision_arbiter_conflict_priority_patch_evidence.py", "contracts/generated/context_pack/MVP4_DECISION_ARBITER_CONFLICT_PRIORITY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- primary blocker selection is deterministic and no longer depends on set iteration
- legacy KILL_SWITCH input is normalized to KILL_SWITCH_ACTIVE
- kill switch, live final guard, reconciliation, risk, data, cost, regime, and min-edge blockers have an explicit order
- PAPER no-trade reason lists use the same priority order as primary_blocker_code
- reconciliation-family blockers force RECONCILE_REQUIRED in the operational PAPER arbiter
- all changed paths remain PAPER/SHADOW analysis only and do not create live permission

known_omissions_by_design:
- no live order submission
- no credential or private API use
- no LIVE_READY snapshot write
- no risk scale-up
- open contract gaps remain open until external evidence or operator reconciliation exists

conflict_resolution_rule:
TRADER_1.md active authority wins over this generated cache. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-05-05T14:55:44Z
