# MVP4_UPBIT_PAPER_BLOCKED_REPAIR_PLAN

context_pack_id: MVP4_UPBIT_PAPER_BLOCKED_REPAIR_PLAN
task_class: MVP4_UPBIT_PAPER_LEDGER_ROLLUP_REBUILD_READY_REPAIR
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-PLAN"]
included_schema_ids: ["trader1.upbit_paper_blocked_repair_plan_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "upbit_paper_blocked_repair_plan_validator", "paper_ledger_rollup_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/upbit_paper_blocked_repair_plan_report.schema.json", "trader1/runtime/paper/upbit_paper_blocked_repair_plan.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_blocked_repair_plan.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_blocked_repair_plan_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_blocked_repair_plan_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_BLOCKED_REPAIR_PLAN.md"]

acceptance_checklist:
- Blocked regenerated replacements are grouped by safe repair lane.
- Operator can distinguish ledger-rollup-ready, missing-cycle-ledger rerun, and recovery-then-ledger blockers.
- Repair planning does not mutate current evidence, delete source artifacts, create long-run evidence, or enable live/scale-up.
- The single ledger-rollup-ready item remains blocked until validator-backed repair evidence exists.

runtime_summary:
- repair_plan_status: BLOCKED
- repair_item_count: 6
- repair_lane_counts: [{"safe_repair_lane": "LEDGER_ROLLUP_REBUILD_READY", "count": 1}, {"safe_repair_lane": "RECOVERY_GUARD_THEN_LEDGER_ROLLUP", "count": 1}, {"safe_repair_lane": "RERUN_RUNTIME_CYCLES_THEN_LEDGER_ROLLUP", "count": 4}]
- ledger_rollup_rebuild_ready_count: 1
- runtime_cycle_rerun_required_count: 5
- recovery_guard_rerun_required_count: 1
- missing_cycle_ledger_jsonl_total_count: 10
- missing_paper_ledger_rollup_artifact_count: 6
- live_order_allowed: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch writes a repair plan only; it does not rebuild ledger rollup artifacts.
- No private exchange/account/API call or credential was used.
- No source report was deleted or overwritten.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T03:41:17Z
