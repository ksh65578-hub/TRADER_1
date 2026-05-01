# MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD

context_pack_id: MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD
task_class: MVP4_WINDOWS_RUNTIME_RECOVERY_CONTINUE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_PARTIAL_WRITE_CRASH_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-WINDOWS-RESTART-RECOVERY-ARTIFACT-PATH-GUARD"]
included_schema_ids: ["trader1.restart_recovery_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "restart_recovery_validator", "runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/core/ledger/restart_recovery.py", "contracts/schema/restart_recovery_report.schema.json", "trader1/validation/mvp0_validators.py", "tests/runtime/test_restart_recovery.py", "tools/emit_windows_restart_recovery_artifact_path_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_WINDOWS_RESTART_RECOVERY_ARTIFACT_PATH_GUARD.md", "system/runtime/upbit/krw_spot/paper/recovery/restart_recovery_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/restart_recovery_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_ledger_rollup_repair_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_repair_reconciliation_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/repairs/mvp4-ledger-jsonl-recovery-ui-refresh-regenerated-current-schema.ledger_rollup_candidate.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Restart recovery PASS requires windows_path_recovery_checked=true.
- Restart recovery PASS requires atomic_write_recovery_checked=true.
- Restart recovery PASS requires partial_write_recovery_checked=true.
- Restart recovery PASS requires stale_lock_recovery_checked=true.
- Recovery artifact paths must be non-empty relative POSIX paths with no drive prefix, backslash, absolute path, or parent traversal.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- recovery_artifact_paths: ["system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/summary.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/heartbeat.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/launcher/root_launcher_report.json"]
- refreshed_dependent_paper_repair_artifacts: ["system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/repairs/mvp4-ledger-jsonl-recovery-ui-refresh-regenerated-current-schema.ledger_rollup_candidate.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_ledger_rollup_repair_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_repair_reconciliation_report.json"]
- negative_cases: drive path, backslash path, parent traversal, missing partial-write evidence, empty artifact paths

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-01T13:28:16Z
