# MVP4_UPBIT_PAPER_PUBLIC_COLLECTOR_PERSISTENT_LOOP

context_pack_id: MVP4_UPBIT_PAPER_PUBLIC_COLLECTOR_PERSISTENT_LOOP
task_class: MVP4_UPBIT_PAPER_PUBLIC_COLLECTOR_PERSISTENT_LOOP
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ['REQ-MVP4-UPBIT-PUBLIC-MARKET-DATA-COLLECTOR', 'REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-BOUNDED', 'REQ-MVP4-PUBLIC-CANONICAL-EVENT-JSONL-RECOVERY', 'REQ-MVP4-PAPER-RUNTIME-COLLECTION-HASH-BINDING', 'REQ-MVP4-EVIDENCE-WRITE-HELPER-ALIAS-AWARE-SCANNER']
included_schema_ids: ["trader1.upbit_public_market_data_collection_report.v1", "trader1.upbit_paper_persistent_loop_report.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: ["upbit_public_market_data_collection_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_cycle_validator"]
included_artifact_ids: ["trader1/runtime/paper/upbit_public_collector.py", "trader1/runtime/paper/upbit_paper_persistent_loop.py", "trader1/runtime/paper/upbit_paper_runtime.py"]
source_section_hashes: see contracts/generated/authority_section_map.json
acceptance_checklist:
- public collection remains public-only and live-blocked
- canonical JSONL partial-write recovery is covered by a negative test
- persistent loop remains bounded and cannot become long-run or promotion evidence
- dashboard receives ledger-backed PAPER values only as display truth
known_omissions_by_design:
- no real Upbit private/account/API-key access
- no MVP-5 live-enabling behavior
- no Binance adapter implementation in this patch
conflict_resolution_rule: TRADER_1.md wins over this generated read cache.
