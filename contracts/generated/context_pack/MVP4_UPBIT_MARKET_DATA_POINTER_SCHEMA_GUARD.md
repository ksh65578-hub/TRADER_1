# MVP4_UPBIT_MARKET_DATA_POINTER_SCHEMA_GUARD

context_pack_id: MVP4_UPBIT_MARKET_DATA_POINTER_SCHEMA_GUARD
task_class: MVP4_UPBIT_MARKET_DATA_POINTER_SCHEMA_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DATA_FRESHNESS", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-MARKET-DATA-POINTER-SCHEMA-GUARD"]
included_schema_ids: ["trader1.upbit_public_market_data_latest_pointer.v1", "trader1.upbit_public_market_data_collection_writer_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "upbit_public_market_data_collection_validator", "runtime_schema_instance_validator", "path_namespace_validator", "single_writer_order_path_validator", "live_final_guard_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/upbit_public_market_data_latest_pointer.schema.json", "contracts/schema/upbit_public_market_data_collection_writer_report.schema.json", "trader1/runtime/paper/upbit_public_collector.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tools/emit_upbit_market_data_pointer_schema_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_MARKET_DATA_POINTER_SCHEMA_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Latest market-data pointer has strict schema and registry entry.
- Collection writer report has strict schema and registry entry.
- Runtime schema instance validator covers generated pointer/writer artifacts.
- Pointer hash mismatch fails closed.
- Writer live flag mutation is blocked.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live Upbit order path
- no credential or private account access
- no LIVE_READY snapshot write
- no MVP-5 promotion

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T16:48:54Z
