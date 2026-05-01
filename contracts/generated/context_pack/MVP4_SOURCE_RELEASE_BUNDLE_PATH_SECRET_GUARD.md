# MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD

context_pack_id: MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD
task_class: MVP4_SOURCE_RELEASE_BUNDLE_HYGIENE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_SECRET_HYGIENE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SOURCE-RELEASE-BUNDLE-PATH-SECRET-GUARD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/security/source_bundle.py", "trader1/validation/mvp0_validators.py", "tests/security/test_source_bundle_security.py", "contracts/security/source_bundle_manifest.json", "tools/emit_source_release_bundle_path_secret_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Source bundle path classification must reject absolute paths, drive paths, dot segments, and parent traversal.
- Shipped package hygiene must treat unsafe path strings as forbidden.
- Secret scan must regenerate the manifest and detect credential-like material in excluded files, including .env.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- unsafe_path_negative_cases: ["contracts/../system/evidence.json", "contracts\\..\\system\\evidence.json", "/contracts/schema/common.defs.schema.json", "C:/TRADER_1/contracts/schema/common.defs.schema.json"]
- included_count: 785
- excluded_count: 1866
- shipped_forbidden_count: 0
- secret_findings_count: 0
- excluded_secret_findings_count: 0
- repo_secret_findings_count: 0

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-01T13:08:15Z
