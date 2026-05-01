# MVP4_UPBIT_PAPER_POST_RERUN_SOURCE_RECONCILIATION_BINDING_GUARD

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_SOURCE_RECONCILIATION_BINDING_GUARD
task_class: MVP4_UPBIT_PAPER_POST_RERUN_SOURCE_RECONCILIATION_BINDING_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-RERUN-SOURCE-RECONCILIATION-BINDING-GUARD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_current_evidence_promotion_guard_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_post_rerun_ledger_rollup_reconciliation_validator", "upbit_paper_post_rerun_current_evidence_promotion_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_post_rerun_current_evidence_promotion_guard_report.schema.json", "trader1/runtime/paper/upbit_paper_post_rerun_current_evidence_promotion_guard.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_post_rerun_current_evidence_promotion_guard.py", "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py", "tests/runtime/test_upbit_paper_post_rerun_reconciliation_decision_audit.py", "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py", "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_review_guidance.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_current_evidence_promotion_guard_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_post_rerun_source_reconciliation_binding_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_SOURCE_RECONCILIATION_BINDING_GUARD.md"]

acceptance_checklist:
- The promotion guard reloads the source post-rerun reconciliation artifact from disk.
- The source artifact's stored reconciliation hash and recomputed hash must match the in-memory source hash.
- Missing, invalid, or hash-mismatched source reconciliation files block the promotion guard.
- Current evidence writes, live permission, promotion, long-run evidence, and scale-up stay false.

known_omissions_by_design:
- This patch is not a current-evidence writer.
- This patch does not resolve POST_RERUN_RECONCILIATION_REQUIRED.
- No credentialed exchange/account/API call, live order, live config mutation, or scale-up was used.

runtime_summary:
- promotion_guard_status: BLOCKED
- source_file_load_status: PASS
- source_file_hash_match: true
- promotion_review_ready_count: 8
- current_evidence_write_allowed_count: 0
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T19:39:09Z
