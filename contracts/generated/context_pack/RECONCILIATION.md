# RECONCILIATION

context_pack_id: RECONCILIATION
task_class: MVP1_SAFE_BOOT_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_RECONCILIATION_CORE_RULES", "SECTION_RECONCILIATION_VALIDATOR_ID", "SECTION_LIVE_READINESS_RECONCILIATION_BLOCKERS", "SECTION_AGENTS_RECONCILIATION_TRUTH", "SECTION_AGENTS_DECISION_RECONCILIATION_PATH", "SECTION_AGENTS_RECONCILIATION_DRY_RUN"]
included_requirement_ids: ["REQ-MVP1-RECONCILIATION-SCAFFOLD"]
included_schema_ids: ["trader1.reconciliation_report.v1", "trader1.validator_result.v1"]
included_validator_ids: ["reconciliation_validator", "ledger_reconciliation_validator"]
included_artifact_ids: ["trader1/runtime/reconciliation/reconciliation.py", "contracts/schema/reconciliation_report.schema.json", "tests/runtime/test_reconciliation.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- matching fresh snapshots still do not create entry or live permission in MVP-1
- stale reconciliation resolves to RECONCILE_REQUIRED
- exchange/internal mismatch resolves to RECONCILE_REQUIRED
- missing ledger or account truth resolves to HARD_TRUTH_MISSING
- namespace mismatch resolves to SNAPSHOT_SCOPE_MISMATCH
- adapter calls and live permission mutations are blocked

known_omissions_by_design:
- no exchange API reconciliation adapter
- no live account query
- no emergency flatten execution
- no live order submission
- retained archive was read only for omitted-detail lookup and cannot create permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T14:50:36Z
