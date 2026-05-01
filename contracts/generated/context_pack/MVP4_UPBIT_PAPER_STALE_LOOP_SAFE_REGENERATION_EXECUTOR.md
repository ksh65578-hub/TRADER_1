# MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-SAFE-REGENERATION-EXECUTOR"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_safe_regeneration_executor_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_reconciliation_validator", "upbit_paper_stale_loop_regeneration_plan_validator", "upbit_paper_stale_loop_execution_guard_validator", "upbit_paper_stale_loop_safe_regeneration_executor_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR.md", "contracts/registry.yaml", "contracts/schema/upbit_paper_stale_loop_safe_regeneration_executor_report.schema.json", "contracts/security/source_bundle_manifest.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-candidate-linkage-cost-model-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-candidate-scorecard-runtime-linkage-binding-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-dashboard-stale-rollup-truth-guard-current-refresh-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-ledger-jsonl-recovery-ui-refresh-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-paper-ledger-rollup-ui-refresh-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-public-rest-transform-loop-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-sequence-regime-guard-loop-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-summary-portfolio-provenance-guard-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-candidate-decision-guard-current-refresh-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-market-data-pointer-schema-guard-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-paper-ledger-rollup-consistency-guard-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-paper-runtime-e2e-consistency-guard-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-public-loop-dashboard-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-recovery-guard-loop-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-runtime-source-hash-guard-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/mvp4-upbit-scorecard-bridge-current-refresh-regenerated-current-schema.persistent_loop_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_safe_regeneration_executor_report.json", "tests/runtime/test_upbit_paper_stale_loop_safe_regeneration_executor.py", "tools/emit_upbit_paper_stale_loop_safe_regeneration_executor_patch_evidence.py", "trader1/runtime/paper/upbit_paper_stale_loop_safe_regeneration_executor.py", "trader1/validation/mvp0_validators.py"]

acceptance_checklist:
- The executor accepts only a PASS execution guard for UPBIT/KRW_SPOT/PAPER.
- It writes current-schema replacement reports with CREATE_NEW_ONLY semantics.
- It retains every source report and never deletes or overwrites stale artifacts.
- It creates no long-run evidence, live readiness, order permission, promotion, or scale-up permission.
- Existing replacement paths block repeated execution.

known_omissions_by_design:
- regenerated artifacts are bounded PAPER schema-repair artifacts, not long-run evidence
- stale source artifacts remain retained for audit and post-regeneration reconciliation
- no private exchange/account/API call or credential was used
- MVP-5 remains blocked on external live-review evidence and operator approval

current_executor_summary:
- executor_status: PASS
- planned_regeneration_item_count: 16
- regenerated_item_count: 16
- skipped_item_count: 0
- replacement_artifact_count: 16
- actual_regeneration_performed: true
- actual_long_run_evidence_created: false
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T01:23:06Z
