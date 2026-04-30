# RUNTIME_WRITE_LOCK_LIVE_OWNER_RECHECK

context_pack_id: RUNTIME_WRITE_LOCK_LIVE_OWNER_RECHECK
task_class: MVP4_RUNTIME_WRITE_LOCK_LIVE_OWNER_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PARTIAL_WRITE_CRASH_RECOVERY", "SECTION_RUNTIME_WRITE_LOCK", "SECTION_RACE_CONDITION_PARTIAL_WRITE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-RUNTIME-WRITE-LOCK-LIVE-OWNER-RECHECK"]
included_schema_ids: ["trader1.root_launcher_report.v1", "trader1.patch_result.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "root_launcher_surface_validator", "single_writer_order_path_validator", "runtime_resource_pressure_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/boot/safe_launcher.py", "tests/runtime/test_safe_launcher.py", "tools/emit_runtime_write_lock_live_owner_recheck_patch_evidence.py", "contracts/generated/context_pack/RUNTIME_WRITE_LOCK_LIVE_OWNER_RECHECK.md", "system/evidence/audit_reports/MVP4_RUNTIME_WRITE_LOCK_LIVE_OWNER_RECHECK_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Runtime write lock never breaks a stale-looking lock while the owner process is still alive.
- Runtime write lock can recover an abandoned stale lock when the owner process is gone.
- Same session duplicate writer remains blocked.
- Launcher/runtime/dashboard artifacts remain namespace scoped.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T08:29:51Z
