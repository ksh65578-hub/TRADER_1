# PARTIAL_WRITE_CRASH_RECOVERY_RECHECK

context_pack_id: PARTIAL_WRITE_CRASH_RECOVERY_RECHECK
task_class: MVP4_PARTIAL_WRITE_CRASH_RECOVERY_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PARTIAL_WRITE_CRASH_RECOVERY", "SECTION_RUNTIME_WRITE_LOCK", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PARTIAL-WRITE-CRASH-RECOVERY-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "root_launcher_surface_validator", "runtime_resource_pressure_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["tools/emit_root_launcher_operator_visibility_patch_evidence.py", "tests/runtime/test_evidence_atomic_write_helpers.py", "tools/emit_partial_write_crash_recovery_recheck_patch_evidence.py", "contracts/generated/context_pack/PARTIAL_WRITE_CRASH_RECOVERY_RECHECK.md", "system/evidence/audit_reports/MVP4_PARTIAL_WRITE_CRASH_RECOVERY_RECHECK_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Evidence/state helper writes use same-directory temp files and os.replace.
- Temp files are cleaned after success or failure.
- JSON serialization failure preserves the previously valid target file.
- Patch evidence generation still passes patch_result runtime validation.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T06:59:59Z
