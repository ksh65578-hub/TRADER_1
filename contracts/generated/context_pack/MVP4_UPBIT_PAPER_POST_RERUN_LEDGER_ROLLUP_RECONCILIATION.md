# MVP4_UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION
task_class: MVP4_UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_ledger_rollup_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_bounded_rerun_staging_executor_validator", "upbit_paper_post_rerun_ledger_rollup_reconciliation_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_post_rerun_ledger_rollup_reconciliation_report.schema.json", "trader1/runtime/paper/upbit_paper_post_rerun_ledger_rollup_reconciliation.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_post_rerun_ledger_rollup_reconciliation.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_ledger_rollup_reconciliation_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_post_rerun_ledger_rollup_reconciliation_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_LEDGER_ROLLUP_RECONCILIATION.md"]

acceptance_checklist:
- Post-rerun reconciliation consumes only the validated bounded staging executor report.
- Candidate rollups are written only under paper_runtime/rerun_candidates_post_rollup and are reused idempotently when hashes match.
- Staged runtime cycle, ledger JSONL, and writer report hashes are verified before a candidate rollup is accepted.
- Current ledger JSONL, latest runtime pointer, persistent loop reports, source artifacts, live permission, promotion, long-run evidence, and scale-up remain immutable.
- Reconciliation remains BLOCKED until a current-evidence promotion guard is implemented.

known_omissions_by_design:
- Candidate rollups are not current evidence and cannot satisfy long-run, promotion, live readiness, or scale-up gates.
- This patch does not mutate current ledger/runtime pointers and does not write LIVE_READY input.
- No private exchange/account/API call or credential was used.

runtime_summary:
- post_rerun_ledger_rollup_status: PASS
- post_rerun_reconciliation_status: BLOCKED
- source_staged_cycle_count: 8
- candidate_item_count: 8
- candidate_rollup_pass_count: 8
- candidate_rollup_written_count: 0
- candidate_rollup_reused_existing_count: 8
- candidate_empty_no_trade_ledger_count: 1
- candidate_current_evidence_usable_count: 0
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T15:20:06Z
