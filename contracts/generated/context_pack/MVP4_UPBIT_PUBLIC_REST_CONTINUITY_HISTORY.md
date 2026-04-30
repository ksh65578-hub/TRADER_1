# MVP4_UPBIT_PUBLIC_REST_CONTINUITY_HISTORY

context_pack_id: MVP4_UPBIT_PUBLIC_REST_CONTINUITY_HISTORY
task_class: MVP4_UPBIT_PUBLIC_REST_CONTINUITY_HISTORY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MARKET_DATA", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LONG_RUN_STABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PUBLIC-REST-CONTINUITY-HISTORY"]
included_schema_ids: ["trader1.upbit_public_rest_continuity_history.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_public_rest_continuity_history_validator", "upbit_public_rest_continuity_validator", "upbit_public_rest_sample_validator", "upbit_public_market_data_collection_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/upbit_public_rest_continuity_history.schema.json", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "trader1/runtime/paper/upbit_public_rest_continuity_history.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_rest_continuity_history.py", "tools/update_upbit_public_rest_continuity_history.py", "tools/emit_upbit_public_rest_continuity_history_patch.py", "contracts/generated/context_pack/MVP4_UPBIT_PUBLIC_REST_CONTINUITY_HISTORY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- public REST continuity attempts are accumulated as PAPER-only history
- corrupt or invalid previous history is quarantined instead of silently erased
- short history never becomes long-run evidence, promotion evidence, LIVE_READY, or scale-up evidence
- latest duplicate/non-advancing attempt remains BLOCKED with operator-visible blocker

known_omissions_by_design:
- continuity history is not official API verification
- continuity history is not read-only account evidence or burn-in evidence
- MVP-5 remains blocked

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-30T12:18:58Z
