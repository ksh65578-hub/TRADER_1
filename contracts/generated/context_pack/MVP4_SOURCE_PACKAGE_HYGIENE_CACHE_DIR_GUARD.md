# MVP4_SOURCE_PACKAGE_HYGIENE_CACHE_DIR_GUARD

context_pack_id: MVP4_SOURCE_PACKAGE_HYGIENE_CACHE_DIR_GUARD
task_class: MVP4_SOURCE_PACKAGE_HYGIENE_CACHE_DIR_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_SECRET_HYGIENE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SOURCE-PACKAGE-HYGIENE-CACHE-DIR-GUARD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/security/source_bundle_denylist.json", "contracts/security/source_bundle_manifest.json", "tests/security/test_source_bundle_security.py", "tools/emit_source_package_hygiene_cache_dir_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_SOURCE_PACKAGE_HYGIENE_CACHE_DIR_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Nested cache directories are denied even when files inside them are not .pyc.
- Source bundle candidate and shipped package hygiene validator both fail closed for cache markers.
- Current repository has zero __pycache__ directories and zero .pyc files.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- included_count: 712
- excluded_count: 1466
- shipped_forbidden_count: 0
- current_pycache_dir_count: 0
- current_pyc_file_count: 0

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T15:24:21Z
