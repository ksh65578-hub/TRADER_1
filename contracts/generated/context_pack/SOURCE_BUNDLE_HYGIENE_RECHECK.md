# SOURCE_BUNDLE_HYGIENE_RECHECK

context_pack_id: SOURCE_BUNDLE_HYGIENE_RECHECK
task_class: MVP4_SOURCE_BUNDLE_HYGIENE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_SECRET_HYGIENE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SOURCE-BUNDLE-HYGIENE-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "source_bundle_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/security/source_bundle_denylist.json", "contracts/security/source_bundle_manifest.json", "tests/security/test_source_bundle_security.py", "tools/emit_source_bundle_hygiene_recheck_patch_evidence.py", "contracts/generated/context_pack/SOURCE_BUNDLE_HYGIENE_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Source bundle candidate excludes contracts/generated/.
- Source bundle candidate excludes contracts/security/source_bundle_manifest.json.
- Source bundle candidate is not self-referential and does not report stale generated read-cache/state as release source.
- secret_scan_validator and source_bundle_hygiene_validator PASS.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- included_count: 530
- excluded_count: 968
- forbidden_generated_count: 0
- self_referential_manifest_included: false
- contains_secret: false

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T08:46:41Z
