# MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RUNTIME_EVIDENCE

context_pack_id: MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RUNTIME_EVIDENCE
task_class: VALIDATOR_IMPLEMENTATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_IDEMPOTENCY", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE"]
included_schema_ids: ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.paper_ledger_rollup_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "paper_ledger_rollup_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "reconciliation_validator", "ledger_reconciliation_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json", "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/upbit_paper_ledger_idempotency_runtime_evidence_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_ledger_idempotency_runtime_evidence_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RUNTIME_EVIDENCE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Current Upbit PAPER ledger idempotency evidence rereads the canonical PAPER ledger rollup source.
- Event counts, fill counts, duplicate event ids, duplicate dedup keys, semantic duplicate events, and filled order keys are recomputed from JSONL.
- Portfolio provenance must match the rollup latest ledger head hash and cycle id.
- Duplicate, escaped, mismatched, or live-mutated evidence remains blocked.

known_omissions_by_design:
- This patch does not resolve post-rerun operator reconciliation guidance.
- This patch does not create long-run evidence, LIVE_READY, live config, credentials, orders, or scale-up permission.
- Dashboard operator visibility for this new idempotency evidence is the next safe task.

runtime_summary:
- runtime_evidence_status: PASS
- idempotency_status: PASS
- reconciliation_status: PASS
- portfolio_provenance_status: PASS
- source_ledger_jsonl_count: 28
- recomputed_ledger_event_count: 168
- duplicate_event_id_count: 0
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T21:57:22Z
