# UPBIT_PAPER_CANDIDATE_DECISION_GUARD

context_pack_id: UPBIT_PAPER_CANDIDATE_DECISION_GUARD
task_class: MVP4_UPBIT_PAPER_CANDIDATE_DECISION_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_PROFIT_CONVERGENCE_REINFORCEMENT", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-CANDIDATE-DECISION-THRESHOLD-GUARD"]
included_schema_ids: ["trader1.upbit_paper_runtime_cycle_report.v1", "trader1.common_defs.v1"]
included_validator_ids: ["upbit_paper_runtime_cycle_validator", "upbit_paper_persistent_loop_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_runtime_cycle_report.schema.json", "trader1/runtime/paper/upbit_paper_runtime.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "contracts/generated/context_pack/UPBIT_PAPER_CANDIDATE_DECISION_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- candidate signal_grade matches signal_strength
- PAPER_ENTRY_REVIEW requires net_ev_after_cost_bps > 5 and signal_strength >= 0.55
- PAPER_ENTRY_REVIEW cannot carry a no-trade reason
- NO_TRADE candidates require the exact threshold failure reason
- threshold-passing candidates cannot be silently suppressed as NO_TRADE
- all outputs remain PAPER-only and live-blocked

known_omissions_by_design:
- no live order submission
- no private account snapshot
- no live readiness claim
- no risk scale-up
- OOS and walk-forward profitability evidence remain blockers

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T14:06:44Z
