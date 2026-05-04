# MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK

context_pack_id: MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK
task_class: MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-STALE-LOOP-REGENERATION-EXECUTION-REQUIRED-RECHECK", "REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK", "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-SAFE-REGENERATION-EXECUTOR", "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_stale_loop_regeneration_execution_guard.v1", "trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1", "trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_reconciliation_validator", "upbit_paper_stale_loop_regeneration_plan_validator", "upbit_paper_stale_loop_execution_guard_validator", "upbit_paper_stale_loop_safe_regeneration_executor_validator", "upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py", "tools/emit_stale_loop_regeneration_execution_required_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK.md"]

acceptance_checklist:
- Confirm execution guard PASS evidence remains pre-execution and source-retaining.
- Confirm safe regeneration executor PASS created 16 current-schema PAPER replacements.
- Confirm source reports remain retained and no delete or overwrite is allowed.
- Confirm generated replacements are not long-run evidence, live evidence, promotion evidence, or scale-up evidence.
- Close STALE_LOOP_REGENERATION_REQUIRED and STALE_LOOP_REGENERATION_EXECUTION_REQUIRED in current state.
- Route next_allowed_task_class to MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK.

execution_recheck_snapshot:
- guard_status: PASS
- executor_status: PASS
- regenerated_item_count: 16
- replacement_artifact_count: 16
- post_regeneration_status: BLOCKED
- post_regeneration_current_evidence_usable_count: 10

known_omissions_by_design:
- This patch does not run regeneration again.
- This patch does not delete or overwrite stale source artifacts.
- This patch does not write current-evidence snapshots, mutate live config, use credentials, place live orders, create long-run evidence, or scale up.
- STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED remains open for the next safe recheck.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-04T03:02:40Z
