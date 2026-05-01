# MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE

context_pack_id: MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE
task_class: MVP4_UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-REPAIR-OPERATOR-QUEUE"]
included_schema_ids: ["trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_blocked_repair_plan_validator", "upbit_paper_ledger_rollup_repair_validator", "upbit_paper_post_repair_reconciliation_validator", "upbit_paper_repair_operator_queue_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/upbit_paper_repair_operator_queue_report.schema.json", "trader1/runtime/paper/upbit_paper_repair_operator_queue.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_repair_operator_queue.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repair_operator_queue_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_repair_operator_queue_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE.md"]

acceptance_checklist:
- Operator queue links blocked repair plan, ledger rollup repair candidate, and post-repair reconciliation hashes.
- It prioritizes the single ledger-candidate-ready item ahead of runtime-cycle and recovery reruns.
- It keeps all repair candidates out of current evidence until operator reconciliation and validator-backed follow-up pass.
- It creates no long-run evidence, live readiness, order permission, promotion, deletion, overwrite, or scale-up permission.

known_omissions_by_design:
- The queue is operator visibility only; it does not repair missing runtime cycle ledgers.
- Repair candidates remain blocked and unusable as current evidence.
- No private exchange/account/API call or credential was used.
- MVP-5 remains blocked on external live-review evidence and operator approval.

runtime_summary:
- queue_status: BLOCKED
- queue_item_count: 6
- ledger_candidate_review_ready_count: 1
- runtime_cycle_rerun_required_count: 5
- recovery_guard_rerun_required_count: 1
- hash_operator_reconciliation_required_count: 1
- candidate_current_evidence_usable_count: 0
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T14:01:15Z
