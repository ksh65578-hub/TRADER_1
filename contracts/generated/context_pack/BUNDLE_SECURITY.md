# BUNDLE_SECURITY

context_pack_id: BUNDLE_SECURITY
task_class: BUNDLE_SECURITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_BUNDLE_SECURITY", "SECTION_PATCH_RESULT"]
included_requirement_ids: ["REQ-MVP0-BUNDLE-SECURITY"]
included_schema_ids: ["trader1.validator_result.v1", "trader1.patch_result.v1"]
included_validator_ids: ["source_bundle_hygiene_validator", "secret_scan_validator"]
included_artifact_ids: ["contracts/security/source_bundle_denylist.json", "contracts/security/source_bundle_manifest.json", "trader1/security/source_bundle.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- retained archive is not read by default
- source bundle candidate forbidden_count is 0
- credential-like material is absent from source bundle candidate
- release package readiness does not imply live_order_ready
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- actual release package build
- external sharing workflow
- live-enabling evidence
- real credential handling

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T12:49:26Z
