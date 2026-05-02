# MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-LEDGER-ROLLUP-RECONCILIATION-RECHECK"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_normalized_reconciliation_recheck_validator", "upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report.schema.json", "trader1/runtime/paper/upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck.py", "tools/emit_upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_patch_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_ledger_rollup_reconciliation_recheck_report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_RECONCILIATION_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Normalized stale-loop ledger-rollup references are checked against actual rollup artifacts.
- Missing ledger-rollup artifacts remain blocked for all candidates.
- No ledger-rollup writes, current-evidence writes, live config, order path, credential path, or scale-up path is enabled.

runtime_summary:
- recheck_status: BLOCKED
- ledger_rollup_recheck_candidate_count: 5
- ledger_rollup_artifact_exists_count: 0
- ledger_rollup_artifact_missing_count: 5
- ledger_rollup_hash_match_count: 0
- ledger_rollup_validator_pass_count: 0
- ledger_rollup_reconciliation_blocked_count: 5
- ledger_rollup_write_allowed_count: 0
- current_evidence_write_allowed_count: 0
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch is recheck-only. It does not regenerate rollup artifacts, rewrite replacements, or promote current evidence.
- It does not create LIVE_READY.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T06:46:25Z
