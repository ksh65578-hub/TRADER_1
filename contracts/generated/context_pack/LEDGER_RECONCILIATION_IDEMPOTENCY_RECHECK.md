# LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK

context_pack_id: LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK
task_class: MVP4_LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-LEDGER-RECONCILIATION-IDEMPOTENCY-RECHECK"]
included_schema_ids: ["trader1.ledger_event.v1", "trader1.intent_wal_event.v1", "trader1.restart_recovery_report.v1", "trader1.reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "ledger_durability_validator", "restart_recovery_validator", "reconciliation_validator", "ledger_reconciliation_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/ledger/execution_ledger.py", "trader1/core/events/intent_wal.py", "contracts/schema/intent_wal_event.schema.json", "contracts/schema/restart_recovery_report.schema.json", "tests/runtime/test_execution_ledger.py", "tests/runtime/test_restart_recovery.py", "tools/emit_ledger_reconciliation_idempotency_recheck_patch_evidence.py", "contracts/generated/context_pack/LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK.md", "system/evidence/audit_reports/MVP4_LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Duplicate semantic ledger events are blocked even if event_id and dedup_key differ.
- Duplicate source ledger event hashes in intent WAL are blocked.
- WAL and restart recovery live/order flags are schema-level false constants.
- Recovery remains PAPER-only and cannot call live order adapters.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T06:53:31Z
