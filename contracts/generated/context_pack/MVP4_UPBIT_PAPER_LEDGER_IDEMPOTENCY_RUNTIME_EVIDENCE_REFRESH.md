# MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_REFRESH

context_pack_id: MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_REFRESH
task_class: VALIDATOR_IMPLEMENTATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE-REFRESH"]
included_schema_ids: ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "paper_ledger_rollup_validator", "reconciliation_validator", "ledger_reconciliation_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator"]
included_artifact_ids: ["tools/run_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py", "tools/emit_upbit_paper_ledger_idempotency_runtime_evidence_refresh_patch_evidence.py", "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py", "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py", "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/upbit_paper_ledger_idempotency_runtime_evidence_report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_REFRESH.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The refresh command regenerates the current Upbit PAPER ledger idempotency runtime evidence report from scoped PAPER runtime inputs.
- Duplicate ledger inputs still produce BLOCKED evidence without live permission.
- The root launcher dashboard binds the refreshed PASS evidence as display truth only.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not resolve LIVE_READY blockers.
- This patch does not use credentials, private exchange endpoints, real orders, live config mutation, or risk scale-up.
- This patch does not claim long-run PAPER/SHADOW evidence or Binance runtime closure.

runtime_summary:
- runtime_evidence_status: PASS
- idempotency_status: PASS
- reconciliation_status: PASS
- portfolio_provenance_status: PASS
- source_ledger_jsonl_count: 28
- recomputed_ledger_event_count: 168
- mismatch_count: 0

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T04:20:03Z
