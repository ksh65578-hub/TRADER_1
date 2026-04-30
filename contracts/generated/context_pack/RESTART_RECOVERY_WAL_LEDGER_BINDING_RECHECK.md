# RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK

context_pack_id: RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK
task_class: MVP4_RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-RESTART-RECOVERY-WAL-LEDGER-BINDING-RECHECK"]
included_schema_ids: ["trader1.intent_wal_event.v1", "trader1.restart_recovery_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "ledger_durability_validator", "restart_recovery_validator", "reconciliation_validator", "ledger_reconciliation_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/core/events/intent_wal.py", "trader1/core/ledger/restart_recovery.py", "contracts/schema/intent_wal_event.schema.json", "tests/runtime/test_restart_recovery.py", "tools/emit_restart_recovery_wal_ledger_binding_recheck_patch_evidence.py", "contracts/generated/context_pack/RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK.md", "system/evidence/audit_reports/MVP4_RESTART_RECOVERY_WAL_LEDGER_BINDING_RECHECK_20260429.md"]

acceptance_checklist:
- WAL source_ledger_event_hash must be sha256 hex.
- WAL source hashes must be a subset of recovered ledger event hashes.
- Every recovered intent ledger event must have a WAL source hash.
- Recovery remains PAPER-only and live/order flags remain false.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T08:23:26Z
