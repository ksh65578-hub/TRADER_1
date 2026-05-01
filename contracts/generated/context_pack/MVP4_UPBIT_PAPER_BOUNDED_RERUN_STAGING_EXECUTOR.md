# MVP4_UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR

context_pack_id: MVP4_UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR
task_class: MVP4_UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-BOUNDED-RERUN-STAGING-EXECUTOR"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_bounded_rerun_staging_executor_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_repair_operator_queue_validator", "upbit_paper_missing_cycle_rerun_guard_validator", "upbit_paper_bounded_rerun_staging_executor_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_bounded_rerun_staging_executor_report.schema.json", "trader1/runtime/paper/upbit_paper_bounded_rerun_staging_executor.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_bounded_rerun_staging_executor.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_bounded_rerun_staging_executor_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_bounded_rerun_staging_executor_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_BOUNDED_RERUN_STAGING_EXECUTOR.md"]

acceptance_checklist:
- Executor consumes the validated missing-cycle rerun guard and stages only eligible PAPER runtime replacement cycles.
- Staged artifacts are written only below paper_runtime/rerun_candidates and are reused idempotently when hashes match.
- Current ledger JSONL, latest runtime pointer, persistent loop reports, source artifacts, live permission, promotion, long-run evidence, and scale-up remain immutable.
- Report remains BLOCKED until post-rerun ledger rollup and reconciliation pass.

known_omissions_by_design:
- This patch does not execute actual reruns; it stages validated replacement cycle artifacts from existing regenerated PAPER runtime evidence.
- Staged candidates are not current evidence and cannot satisfy long-run, promotion, live readiness, or scale-up gates.
- Post-staging ledger rollup and reconciliation remain required.
- No private exchange/account/API call or credential was used.

runtime_summary:
- executor_status: BLOCKED
- staging_status: PASS
- ready_guard_item_count: 4
- recovery_guard_blocked_item_count: 1
- eligible_missing_cycle_count: 8
- staged_cycle_count: 8
- staged_artifact_count: 24
- staging_written_artifact_count: 0
- staging_reused_existing_artifact_count: 24
- staged_current_evidence_usable_count: 0
- actual_rerun_executed: false
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T14:57:18Z
