# MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE

context_pack_id: MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE
task_class: MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-STRATEGY-REGIME-COST-RUNTIME-LINKAGE"]
included_schema_ids: ["trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_paper_runtime_cycle_validator", "upbit_public_market_data_collection_validator", "upbit_paper_persistent_loop_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_runtime_cycle_report.schema.json", "trader1/runtime/paper/upbit_paper_runtime.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "trader1/validation/mvp0_validators.py", "tools/emit_strategy_regime_cost_runtime_linkage_patch_evidence.py", "contracts/generated/context_pack/MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- runtime_public_market_data_hash must match the exact public market data payload
- feature_snapshot_hash must match the recomputed feature snapshot
- report regime must match the recomputed feature regime
- every strategy candidate must use the runtime symbol and runtime regime
- candidate spread cost must match the feature spread used by the runtime cycle
- strategy_regime_cost_linkage must bind runtime data hash, feature hash, selected candidate, cost sum, net EV, and live-blocked flags
- selected_candidate must be present in strategy_candidates
- selected_candidate must match the highest net_ev_after_cost_bps candidate
- candidate expected_cost_bps must equal fee, slippage, spread, impact, and latency components
- candidate net_ev_after_cost_bps must equal expected_edge_bps minus expected_cost_bps
- sizing_decision.strategy_unit_id must match selected_candidate.candidate_id
- bounded PAPER runtime rewrites current runtime artifacts without live permission

known_omissions_by_design:
- static PAPER cost model is not live-readiness evidence
- long-run real market evidence, read-only account evidence, and operator approval remain blockers
- Binance adapter/futures implementation remains later-stage/surface-only work

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-05-01T12:13:57Z
