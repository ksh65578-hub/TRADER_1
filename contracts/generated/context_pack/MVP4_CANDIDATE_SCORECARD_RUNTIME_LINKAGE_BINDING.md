# MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING

context_pack_id: MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING
task_class: MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PROFIT_CONVERGENCE_REINFORCEMENT", "SECTION_OPTIMIZER_OBJECTIVE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-CANDIDATE-SCORECARD-RUNTIME-LINKAGE-BINDING"]
included_schema_ids: ["trader1.candidate_scorecard.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "candidate_scorecard_validator", "candidate_scorecard_net_ev_validator", "upbit_paper_runtime_cycle_validator", "upbit_paper_persistent_loop_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/candidate_scorecard.schema.json", "trader1/research/profitability/candidate_scorecard.py", "trader1/validation/mvp0_validators.py", "tests/research/test_candidate_scorecard_from_runtime.py", "tests/validators/test_candidate_scorecard_net_ev_validator.py", "tests/validators/fixtures/candidate_scorecard_net_ev_pass.json", "tests/validators/fixtures/candidate_scorecard_net_ev_raw_cost_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_live_flag_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_missing_oos_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_live_ready_wording_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_missing_robustness_sources_fail.json", "tests/validators/fixtures/candidate_scorecard_net_ev_mismatched_robustness_sources_fail.json", "tools/emit_candidate_scorecard_runtime_linkage_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING.md"]

acceptance_checklist:
- candidate_scorecard carries source_runtime_cycle_id and source_runtime_cycle_hash
- PAPER ranking eligibility requires OOS, walk-forward, and bootstrap evidence ids linked to the same runtime cycle hash
- mismatched robustness evidence remains non-ranking or FAIL/BLOCKED
- optimizer/convergence cannot create live permission, LIVE_READY, or scale-up

known_omissions_by_design:
- no live-enabling evidence
- no private account or credential use
- no long-run live review claim
- robustness evidence remains required before ranking eligibility

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T22:55:53Z
