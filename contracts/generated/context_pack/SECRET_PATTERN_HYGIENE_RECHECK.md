# SECRET_PATTERN_HYGIENE_RECHECK

context_pack_id: SECRET_PATTERN_HYGIENE_RECHECK
task_class: MVP4_SECRET_PATTERN_HYGIENE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SECRET_HYGIENE", "SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SECRET-PATTERN-HYGIENE-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "source_bundle_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/security/source_bundle.py", "tests/security/test_source_bundle_security.py", "contracts/security/source_bundle_manifest.json", "tools/emit_secret_pattern_hygiene_recheck_patch_evidence.py", "contracts/generated/context_pack/SECRET_PATTERN_HYGIENE_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Secret scanner detects AWS-style underscored environment key assignments.
- Secret scanner detects Authorization Bearer headers.
- Secret scanner detects JWT-like literals.
- Source bundle candidate still contains no credential-like material.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- included_count: 530
- excluded_count: 977
- secret_findings_count: 0
- covered_secret_shapes: ["AWS_STYLE_SECRET_ACCESS_KEY_ASSIGNMENT", "AUTHORIZATION_BEARER_HEADER", "JWT_LITERAL", "AWS_AKIA_ACCESS_KEY", "PRIVATE_KEY_BLOCK"]

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T08:51:41Z
