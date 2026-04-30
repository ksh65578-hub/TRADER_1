# MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE

context_pack_id: MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE
task_class: MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MARKET_DATA", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PUBLIC-REST-CONTINUITY-EVIDENCE"]
included_schema_ids: ["trader1.upbit_public_rest_continuity_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_public_rest_continuity_validator", "upbit_public_rest_sample_validator", "upbit_public_market_data_collection_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/upbit_public_rest_continuity_report.schema.json", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "trader1/runtime/paper/upbit_public_rest_continuity.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_rest_continuity.py", "tools/run_upbit_public_rest_continuity_check.py", "tools/emit_upbit_public_rest_continuity_evidence_patch.py", "contracts/generated/context_pack/MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- repeated public REST samples are PAPER continuity evidence only
- repeated latest candle timestamp blocks continuity as DATA_QUALITY_INSUFFICIENT
- network failure is safe BLOCKED evidence, not runtime crash
- continuity cannot load credentials, call private/order endpoints, submit orders, or set live/scale flags

known_omissions_by_design:
- short continuity sample is not long-run evidence
- short continuity sample is not official API verification or account read-only evidence
- MVP-5 remains blocked

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-30T12:06:43Z
