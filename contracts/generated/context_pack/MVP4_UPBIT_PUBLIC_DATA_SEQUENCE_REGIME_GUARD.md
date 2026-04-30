# MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD

context_pack_id: MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD
task_class: MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PUBLIC-DATA-SEQUENCE-REGIME-GUARD"]
included_schema_ids: ["trader1.upbit_public_market_data_collection_report.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_public_market_data_collection_validator", "upbit_paper_runtime_cycle_validator", "upbit_paper_persistent_loop_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/adapters/upbit/market_data.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "tools/emit_upbit_public_data_sequence_regime_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- public candle timestamps must be strictly increasing after canonicalization
- duplicate or out-of-order candle timestamps block with RECONCILIATION_REQUIRED
- risk-off/downtrend PAPER runtime cycle remains NO_TRADE and writes no fill ledger
- no live, private, credential, order, or scale-up behavior is introduced

known_omissions_by_design:
- deterministic sequence/regime tests are not long-run live evidence
- real public REST sampling and long-run PAPER evidence remain future safe work
- MVP-5 remains blocked

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-30T11:46:36Z
