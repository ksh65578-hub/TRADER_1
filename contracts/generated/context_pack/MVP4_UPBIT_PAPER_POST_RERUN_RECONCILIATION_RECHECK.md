# MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK
task_class: MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_IDEMPOTENCY", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-RECHECK"]
included_schema_ids: ["trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1", "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "upbit_paper_post_rerun_current_evidence_closure_recheck_validator", "upbit_paper_post_rerun_reconciliation_repair_path_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_post_rerun_current_evidence_closure_recheck_report.schema.json", "trader1/runtime/paper/upbit_paper_post_rerun_current_evidence_closure_recheck.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_post_rerun_current_evidence_closure_recheck.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_current_evidence_closure_recheck_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/upbit_paper_ledger_idempotency_runtime_evidence_report.json", "contracts/security/source_bundle_manifest.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK.md", "tools/emit_upbit_paper_post_rerun_reconciliation_recheck_patch_evidence.py"]

acceptance_checklist:
- post-rerun closure recheck exposes ledger runtime-depth source fields
- ledger PASS requires persistent-loop validation/hash PASS and ledger-head cycle binding
- source/runtime public market data hashes must match and canonical depth must be present
- strategy/regime/cost linkage live and scale flags remain false
- POST_RERUN_RECONCILIATION_REQUIRED remains primary and current-evidence writes remain blocked

audit_status: PASS

known_omissions_by_design:
- This patch is not a current-evidence writer, LIVE_READY patch, live config mutation, credential path, live order path, or scale-up patch.
- It does not resolve POST_RERUN_RECONCILIATION_REQUIRED; it makes the recheck fail closed on runtime-depth regressions.

runtime_summary:
- recheck_status: BLOCKED_POST_RERUN_CLOSURE_CONFIRMED
- current_evidence_bridge_status: BLOCKED_BY_POST_RERUN_CLOSURE
- ledger_source_runtime_depth_status: PASS
- ledger_head_cycle_in_persistent_loop: True
- ledger_source_runtime_input_role: PUBLIC_MARKET_DATA_COLLECTION
- current_evidence_write_allowed: false
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-03T14:08:01Z
