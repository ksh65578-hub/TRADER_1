# UPBIT_PAPER_RUNTIME_SCORECARD_BRIDGE

context_pack_id: UPBIT_PAPER_RUNTIME_SCORECARD_BRIDGE
task_class: MVP4_UPBIT_PAPER_RUNTIME_SCORECARD_BRIDGE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_PROFIT_CONVERGENCE_REINFORCEMENT", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-RUNTIME-SCORECARD-BRIDGE"]
included_schema_ids: ["trader1.candidate_scorecard.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: ["candidate_scorecard_validator", "candidate_scorecard_net_ev_validator", "upbit_paper_runtime_cycle_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/research/profitability/__init__.py", "trader1/research/profitability/candidate_scorecard.py", "trader1/validation/mvp0_validators.py", "tests/research/test_candidate_scorecard_from_runtime.py", "contracts/generated/context_pack/UPBIT_PAPER_RUNTIME_SCORECARD_BRIDGE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Upbit PAPER runtime cycle can generate candidate_scorecard.v1 artifact
- generated scorecard uses NET_EV_AFTER_COST
- runtime-only scorecard remains PAPER_EVIDENCE_COLLECTION_ONLY until OOS/walk-forward/bootstrap/overfit evidence exists
- scorecard cannot create LIVE_READY, live_order_allowed, can_live_trade, or scale_up_allowed
- invalid runtime cycle cannot become scorecard source evidence

known_omissions_by_design:
- no OOS PASS claim
- no walk-forward PASS claim
- no bootstrap PASS claim
- no live readiness claim
- no live order or private account call

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T14:18:58Z
