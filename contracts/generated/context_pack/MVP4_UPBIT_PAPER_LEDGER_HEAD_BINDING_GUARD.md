# MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD

context_pack_id: MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD
task_class: MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_EVIDENCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LEDGER-HEAD-BINDING-GUARD"]
included_schema_ids: ["trader1.paper_ledger_rollup_report.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.patch_result.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "paper_ledger_rollup_validator", "ledger_durability_validator", "ledger_reconciliation_validator", "upbit_paper_persistent_loop_validator", "runtime_schema_instance_validator", "path_namespace_validator", "single_writer_order_path_validator", "live_final_guard_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/paper_ledger_rollup_report.schema.json", "trader1/runtime/ledger/paper_ledger_rollup.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_paper_ledger_rollup.py", "tools/emit_upbit_paper_ledger_head_binding_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER ledger rollup records duplicate_ledger_path_count and blocks explicit duplicate input paths.
- PAPER ledger rollup records latest ledger head report path, hash, cycle, event count, match status, and mismatch count.
- Session-cycle glob rollups require latest_paper_ledger_head.json binding PASS and portfolio source cycle alignment.
- Explicit scoped repair/rerun rollups use terminal ledger validation, set ledger_input_scope=EXPLICIT_SCOPED_PATHS, and must not claim latest head binding.
- Missing or mismatched latest_paper_ledger_head.json blocks session-cycle rollup review.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no long-run evidence eligibility is created
- no live Upbit order path
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-01T19:25:11Z
