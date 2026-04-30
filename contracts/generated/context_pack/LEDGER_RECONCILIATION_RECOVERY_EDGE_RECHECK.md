# LEDGER_RECONCILIATION_RECOVERY_EDGE_RECHECK

context_pack_id: LEDGER_RECONCILIATION_RECOVERY_EDGE_RECHECK
task_class: MVP4_LEDGER_RECONCILIATION_RECOVERY_EDGE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_IDEMPOTENCY", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-LEDGER-RECONCILIATION-RECOVERY-EDGE-RECHECK"]
included_schema_ids: ["trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "reconciliation_validator", "ledger_reconciliation_validator", "restart_recovery_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/reconciliation/reconciliation.py", "trader1/core/ledger/restart_recovery.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_reconciliation.py", "tests/runtime/test_restart_recovery.py", "tools/emit_ledger_reconciliation_recovery_edge_recheck_patch_evidence.py", "contracts/generated/context_pack/LEDGER_RECONCILIATION_RECOVERY_EDGE_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Reconciliation validator recomputes snapshot mismatch instead of trusting reported PASS.
- Reconciliation validator verifies snapshot body/hash consistency.
- Restart recovery validator blocks crafted PASS when single_writer_recovered=false.
- Restart recovery validator fails recovered flag inconsistency.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- crafted_mismatch_status: BLOCKED
- crafted_mismatch_blocker: RECONCILIATION_REQUIRED
- snapshot_hash_mismatch_status: FAIL
- no_single_writer_status: BLOCKED
- recovered_flag_mismatch_status: FAIL

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T09:14:18Z
