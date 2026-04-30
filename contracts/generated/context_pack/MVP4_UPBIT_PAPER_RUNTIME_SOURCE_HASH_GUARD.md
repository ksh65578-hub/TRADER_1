# MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD
task_class: MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DATA_FRESHNESS", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-RUNTIME-SOURCE-HASH-GUARD"]
included_schema_ids: ["trader1.upbit_public_market_data_collection_report.v1", "trader1.upbit_paper_runtime_cycle_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "upbit_public_market_data_collection_validator", "upbit_paper_runtime_cycle_validator", "upbit_paper_persistent_loop_validator", "runtime_schema_instance_validator", "path_namespace_validator", "single_writer_order_path_validator", "live_final_guard_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/upbit_public_market_data_collection_report.schema.json", "contracts/schema/upbit_paper_runtime_cycle_report.schema.json", "trader1/runtime/paper/upbit_public_collector.py", "trader1/runtime/paper/upbit_paper_runtime.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "tools/emit_upbit_paper_runtime_source_hash_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_SOURCE_HASH_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Upbit public collection report includes public_market_data_hash.
- Upbit PAPER runtime cycle includes source_public_market_data_hash when bound to a collection report.
- Collection-bound runtime recomputes market data hash before accepting payload.
- Latest collection pointer and writer report expose public_market_data_hash for operator/audit traceability.
- Negative fixture mutates public_market_data after collection binding and fails closed.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live Upbit order path
- no private account snapshot
- no credential or API key load
- no LIVE_READY snapshot write
- no MVP-5 promotion

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T16:30:07Z
