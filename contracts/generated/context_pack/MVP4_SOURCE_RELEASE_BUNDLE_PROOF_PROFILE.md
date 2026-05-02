# MVP4_SOURCE_RELEASE_BUNDLE_PROOF_PROFILE

context_pack_id: MVP4_SOURCE_RELEASE_BUNDLE_PROOF_PROFILE
task_class: MVP4_SOURCE_RELEASE_BUNDLE_PROOF_PROFILE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_TEST_PROOF", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SOURCE-RELEASE-BUNDLE-PROOF-PROFILE"]
included_schema_ids: ["trader1.source_release_proof_profile_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "bytecode_free_syntax_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["pyproject.toml", "contracts/schema/source_release_proof_profile_report.schema.json", "tools/run_source_release_proof_profile.py", "tools/run_bundle_security_validators.py", "tools/emit_source_release_bundle_proof_profile_patch_evidence.py", "tests/runtime/test_source_release_proof_profile.py", "contracts/security/source_bundle_manifest.json", "contracts/generated/context_pack/MVP4_SOURCE_RELEASE_BUNDLE_PROOF_PROFILE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- tools/run_source_release_proof_profile.py produces one machine-readable bounded release proof report.
- The profile runs cache-proof pytest, source bundle manifest build, bundle/security validators, patch/runtime schema validators, live final guard validators, and bytecode-free syntax check.
- The profile fails on command failure, timeout, cache artifacts, shipped forbidden artifacts, source secrets, or live flag drift.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- release_profile_status: PASS
- release_profile_command_pass_count: 7/7
- cache_artifact_count: 0
- shipped_forbidden_count: 0
- contains_secret: False

known_omissions_by_design:
- no release zip build
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-02T03:06:54Z
