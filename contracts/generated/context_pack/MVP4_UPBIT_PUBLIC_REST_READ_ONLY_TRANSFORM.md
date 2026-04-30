# MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM

context_pack_id: MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM
task_class: MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PUBLIC-REST-READ-ONLY-TRANSFORM"]
included_schema_ids: ["trader1.upbit_public_market_data_collection_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_public_market_data_collection_validator", "upbit_paper_runtime_cycle_validator", "upbit_paper_persistent_loop_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/adapters/upbit/market_data.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tools/emit_upbit_public_rest_read_only_transform_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Upbit public REST candle payload shape maps into canonical PAPER candle data.
- Approved public endpoint identity is api.upbit.com/v1/candles/minutes/1.
- Authorization headers, private endpoint flags, and order endpoint flags are blocked.
- Duplicate candle timestamps require reconciliation.
- Bounded PAPER runtime can run from PUBLIC_REST_READ_ONLY-shaped inputs while live-blocked.

known_omissions_by_design:
- The required test path uses deterministic public REST-shaped payloads, not mandatory live network access.
- Real public network sampling remains optional operator evidence and is not LIVE_READY evidence.
- No account, private stream, credential, or order endpoint is used.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-30T11:39:52Z
