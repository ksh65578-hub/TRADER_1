# LIVE_BLOCKED_NEGATIVE_RECHECK

context_pack_id: LIVE_BLOCKED_NEGATIVE_RECHECK
task_class: MVP4_LIVE_BLOCKED_NEGATIVE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LIVE_BLOCKED_TEST", "SECTION_LIVE_FINAL_GUARD", "SECTION_ORDER_PATH_GUARD"]
included_requirement_ids: ["REQ-MVP4-LIVE-BLOCKED-NEGATIVE-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "live_blocked_scaffold_validator", "live_blocked_negative_matrix_validator", "single_writer_order_path_validator", "strategy_direct_order_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/safety/live_order_gate.py", "tests/live_blocked/fixtures/live_blocked_matrix.json", "tests/live_blocked/test_live_blocked_scaffold.py", "tests/live_blocked/test_order_path_guard.py", "tools/emit_live_blocked_negative_recheck_patch_evidence.py", "contracts/generated/context_pack/LIVE_BLOCKED_NEGATIVE_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- live_blocked_matrix covers every BLOCKED_CASES key.
- spoofed all-live-true input remains BLOCKED.
- spoofed live_enabling_patch_valid input remains BLOCKED.
- live order gateway never calls the adapter before LIVE_ENABLING evidence.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- blocked_case_count: 25
- matrix_case_count: 25
- spoof_cases_present: true
- missing_from_matrix: []
- mismatched_codes: []

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T08:56:24Z
