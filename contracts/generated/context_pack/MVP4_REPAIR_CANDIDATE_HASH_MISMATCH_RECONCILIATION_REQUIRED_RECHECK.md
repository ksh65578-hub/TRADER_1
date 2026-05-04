# MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK

context_pack_id: MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK
task_class: MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-REPAIR-CANDIDATE-HASH-MISMATCH-RECONCILIATION-REQUIRED-RECHECK", "REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK", "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION", "REQ-MVP4-UPBIT-PAPER-REPAIR-OPERATOR-QUEUE"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1", "trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_post_repair_reconciliation_validator", "upbit_paper_repair_operator_queue_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py", "tools/emit_repair_candidate_hash_mismatch_reconciliation_required_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK.md"]

acceptance_checklist:
- Confirm the repair candidate hash mismatch is caused by a missing source expected rollup artifact.
- Confirm the candidate rollup hash self-check still passes but cannot become current evidence.
- Confirm the repair operator queue marks exactly one item review-ready and hash-reconciliation-required.
- Route next_allowed_task_class to MVP4_BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION_RECHECK without resolving the live-blocking gaps.
- Keep live orders, live config mutation, current evidence mutation, source deletion, and scale-up blocked.

hash_mismatch_snapshot:
- replacement_loop_id: mvp4-ledger-jsonl-recovery-ui-refresh-regenerated-current-schema
- post_repair_reconciliation_status: BLOCKED
- post_repair_hash_reconciliation_status: SOURCE_EXPECTED_ROLLUP_ARTIFACT_MISSING
- post_repair_source_loop_expected_rollup_artifact_load_status: MISSING
- repair_operator_queue_status: BLOCKED
- repair_operator_queue_hash_operator_reconciliation_required_count: 1
- repair_operator_queue_candidate_current_evidence_usable_count: 0

known_omissions_by_design:
- This patch does not fabricate the missing expected rollup artifact.
- This patch does not reconcile the hash mismatch by operator assertion.
- This patch does not write current evidence, mutate live config, use credentials, place live orders, or scale up.
- The hash mismatch gap remains open until a separate validator-backed reconciliation or rerun path resolves it.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-04T01:48:53Z
