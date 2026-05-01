# MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE
task_class: MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD", "AGENTS_0G.14"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-RUNTIME-LEDGER-RECONCILIATION-EVIDENCE"]
included_schema_ids: ["trader1.paper_ledger_rollup_report.v1", "trader1.ledger_event.v1", "trader1.patch_result.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "paper_ledger_rollup_validator", "ledger_durability_validator", "runtime_schema_instance_validator", "review_plan_reflection_ledger_validator", "path_namespace_validator", "single_writer_order_path_validator", "live_final_guard_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/core/ledger/paper_ledger.py", "trader1/runtime/ledger/paper_ledger_rollup.py", "trader1/validation/mvp0_validators.py", "contracts/schema/paper_ledger_rollup_report.schema.json", "tests/runtime/test_paper_ledger_rollup.py", "tools/emit_upbit_paper_runtime_ledger_reconciliation_evidence_patch.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Filled Upbit PAPER orders require intent, budget reservation, submit started, submitted, ack, and fill lifecycle records.
- PAPER ledger rollup records lifecycle_incomplete_order_count.
- Incomplete lifecycle fixtures block with RECONCILIATION_REQUIRED.
- Current review addendum files are reflected into this audit, state, requirement mapping, and patch evidence before deletion.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live Upbit order path
- no credential or private account access
- no LIVE_READY snapshot write
- no MVP-5 promotion
- Binance spot/futures remain surface/scaffold gaps

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-01T12:03:06Z
