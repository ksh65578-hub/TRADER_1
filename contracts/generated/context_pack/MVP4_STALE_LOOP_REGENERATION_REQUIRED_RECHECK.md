# MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK

context_pack_id: MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK
task_class: MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-STALE-LOOP-REGENERATION-REQUIRED-RECHECK", "REQ-MVP4-REGENERATED-CURRENT-BLOCKED-REPAIRS-REQUIRE-LEDGER-RECOVERY-RECONCILIATION-RECHECK", "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION", "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-POLICY"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_stale_loop_regeneration_plan.v1", "trader1.upbit_paper_stale_loop_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_reconciliation_validator", "upbit_paper_stale_loop_regeneration_plan_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "tests/contract/test_stale_loop_regeneration_required_recheck.py", "tools/emit_stale_loop_regeneration_required_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_STALE_LOOP_REGENERATION_REQUIRED_RECHECK.md"]

acceptance_checklist:
- Confirm the stale-loop regeneration plan remains READY_FOR_SAFE_PAPER_REGENERATION.
- Confirm all legacy schema-drift sources map to source-preserving PAPER replacement paths.
- Confirm no stale source is deleted, overwritten, promoted, live-enabled, current-evidence usable, or scale-up enabled.
- Confirm actual_regeneration_performed=false and execution remains a separate required step.
- Route next_allowed_task_class to MVP4_STALE_LOOP_REGENERATION_EXECUTION_REQUIRED_RECHECK.
- Keep live orders, live config mutation, source deletion, current evidence mutation, long-run evidence, and scale-up blocked.

stale_loop_regeneration_snapshot:
- plan_status: READY_FOR_SAFE_PAPER_REGENERATION
- source_loop_report_count: 17
- source_current_accepted_count: 1
- source_excluded_count: 16
- legacy_schema_drift_count: 16
- regeneration_item_count: 16
- operator_review_item_count: 0
- duplicate_replacement_path_count: 0
- overwrite_or_delete_count: 0
- actual_regeneration_performed: false

known_omissions_by_design:
- This patch does not execute stale-loop regeneration.
- This patch does not write replacement persistent-loop reports.
- This patch does not delete or overwrite stale source artifacts.
- This patch does not create long-run evidence, write current evidence, mutate live config, use credentials, place live orders, or scale up.
- STALE_LOOP_REGENERATION_REQUIRED remains open until executor evidence is reconciled.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-04T02:41:23Z
