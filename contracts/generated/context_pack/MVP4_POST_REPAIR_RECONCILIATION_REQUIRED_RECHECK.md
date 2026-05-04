# MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK

context_pack_id: MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK
task_class: MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-POST-REPAIR-RECONCILIATION-REQUIRED-RECHECK", "REQ-MVP4-PATCH-RESULT-VALIDATOR-RUN-GAP-NEXT-TASK-RESTORE", "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION", "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION-OPERATOR-UX-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_post_repair_reconciliation_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["tests/contract/test_post_repair_reconciliation_required_recheck.py", "tools/emit_post_repair_reconciliation_required_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_POST_REPAIR_RECONCILIATION_REQUIRED_RECHECK.md"]

acceptance_checklist:
- Confirm POST_REPAIR_RECONCILIATION_REQUIRED remains open and live-blocking.
- Confirm the specific unresolved item blocker is REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED.
- Route next_allowed_task_class to MVP4_REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED_RECHECK.
- Keep current evidence mutation, live orders, live config mutation, and scale-up blocked.

post_repair_snapshot:
- post_repair_reconciliation_status: BLOCKED
- post_repair_reconciliation_item_count: 1
- post_repair_source_loop_expected_rollup_hash_mismatch_count: 1
- post_repair_candidate_current_evidence_usable_count: 0
- post_repair_primary_item_blocker_code: REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED

known_omissions_by_design:
- This patch does not resolve post-repair reconciliation.
- This patch does not write current evidence, mutate live config, use credentials, place live orders, or scale up.
- The hash mismatch gap remains open for a follow-up recheck.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-04T01:29:13Z
