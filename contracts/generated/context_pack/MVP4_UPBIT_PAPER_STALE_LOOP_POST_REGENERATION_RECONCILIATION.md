# MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_RECONCILIATION

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_RECONCILIATION
task_class: MVP4_UPBIT_PAPER_REGENERATED_BLOCKED_REPAIR_RECONCILIATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_reconciliation_validator", "upbit_paper_stale_loop_regeneration_plan_validator", "upbit_paper_stale_loop_execution_guard_validator", "upbit_paper_stale_loop_safe_regeneration_executor_validator", "upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_stale_loop_post_regeneration_reconciliation_report.schema.json", "contracts/registry.yaml", "trader1/runtime/paper/upbit_paper_stale_loop_post_regeneration_reconciliation.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_post_regeneration_reconciliation_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_stale_loop_post_regeneration_reconciliation_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_POST_REGENERATION_RECONCILIATION.md"]

acceptance_checklist:
- Post-regeneration reconciliation reads the safe executor output and verifies every source was retained.
- It accepts only regenerated current-schema replacements that validate PASS.
- It keeps schema-repaired replacements with RECONCILIATION_REQUIRED excluded from current evidence.
- It ignores source/replacement lineage duplicates and checks duplicate runtime hashes only among usable replacements.
- It creates no long-run evidence, live readiness, order permission, promotion, deletion, overwrite, or scale-up permission.

known_omissions_by_design:
- 6 generated replacements remain BLOCKED by ledger/recovery reconciliation gaps.
- No source report was deleted or overwritten.
- No private exchange/account/API call or credential was used.
- MVP-5 remains blocked on external live-review evidence and operator approval.

runtime_summary:
- post_reconciliation_status: BLOCKED
- planned_regeneration_item_count: 16
- regenerated_current_accepted_count: 10
- regenerated_current_blocked_reconciliation_count: 6
- current_evidence_usable_count: 10
- excluded_from_current_evidence_count: 6
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T01:51:30Z
