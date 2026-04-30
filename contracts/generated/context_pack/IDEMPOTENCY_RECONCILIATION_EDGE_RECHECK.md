# IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK

context_pack_id: IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK
task_class: MVP4_IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_IDEMPOTENCY", "SECTION_RECONCILIATION", "SECTION_ORDER_PATH_GUARD", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-IDEMPOTENCY-RECONCILIATION-EDGE-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "single_writer_order_path_validator", "strategy_direct_order_validator", "ledger_reconciliation_validator", "restart_recovery_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/execution/live_order_gateway.py", "trader1/validation/mvp0_validators.py", "tests/live_blocked/test_order_path_guard.py", "tools/emit_idempotency_reconciliation_edge_recheck_patch_evidence.py", "contracts/generated/context_pack/IDEMPOTENCY_RECONCILIATION_EDGE_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Every ambiguous idempotency state is blocked by RECONCILIATION_REQUIRED before any adapter submit.
- Same-identifier ambiguous transport states require reconciliation before submit.
- Ambiguous states without an original identifier require reconciliation before submit.
- Spoofed all-green live gate inputs cannot downgrade reconciliation into LIVE_ENABLING_EVIDENCE_MISSING.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- same_identifier_primary_blocker: RECONCILIATION_REQUIRED
- same_identifier_final_decision: RECONCILE_REQUIRED
- missing_original_primary_blocker: RECONCILIATION_REQUIRED
- missing_original_final_decision: RECONCILE_REQUIRED

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T09:07:17Z
