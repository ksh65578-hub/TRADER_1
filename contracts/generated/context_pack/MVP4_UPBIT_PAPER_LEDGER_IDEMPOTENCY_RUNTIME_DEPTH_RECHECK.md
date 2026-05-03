# MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK

context_pack_id: MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK
task_class: MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_STRATEGY_REGIME_COST_RUNTIME_LINKAGE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-DEPTH-RECHECK"]
included_schema_ids: ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.upbit_paper_persistent_loop_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "upbit_paper_persistent_loop_validator", "paper_ledger_rollup_validator", "reconciliation_validator", "ledger_reconciliation_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json", "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py", "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py", "tools/emit_upbit_paper_ledger_idempotency_runtime_depth_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- ledger idempotency evidence validates the canonical persistent-loop source hash and status
- ledger head cycle id must exist in persistent loop cycle_results
- the matching cycle must be public-market-data backed with source/runtime hash equality and canonical depth
- strategy/regime/cost linkage live or scale-up flags remain blocked
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

audit_status: PASS

known_omissions_by_design:
- no runtime root output is staged by this contract/evidence patch
- no long-run evidence eligibility, LIVE_READY snapshot, live order path, credential use, live config mutation, or scale-up is introduced
- post-rerun reconciliation and stale-loop regeneration blockers remain separate follow-up work

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-03T13:22:09Z
