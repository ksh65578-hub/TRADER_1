# MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-LEDGER-INPUT-SCOPE-REPAIR-PLAN"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_ledger_input_scope_repair_plan_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_ledger_rollup_executor_reconciliation_recheck_validator", "upbit_paper_stale_loop_ledger_input_scope_repair_plan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_stale_loop_ledger_input_scope_repair_plan_report.schema.json", "trader1/runtime/paper/upbit_paper_stale_loop_ledger_input_scope_repair_plan.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_ledger_input_scope_repair_plan.py", "tools/emit_upbit_paper_stale_loop_ledger_input_scope_repair_plan_patch_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_ledger_input_scope_repair_plan_report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_INPUT_SCOPE_REPAIR_PLAN.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Four strict-scope-blocked candidates are mapped to isolated candidate roots.
- Eight staged ledger JSONL inputs are planned for isolated canonical mirror paths.
- No candidate mirror write, current canonical ledger write, target rollup write, current evidence write, live permission, or scale-up permission is enabled.

runtime_summary:
- plan_status: READY_PLAN_ONLY
- repair_plan_candidate_count: 4
- planned_cycle_count: 8
- repair_cycle_ready_count: 8
- planned_mirror_ledger_count: 8
- current_canonical_ledger_write_allowed_count: 0
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch is plan-only. It does not copy ledger files into isolated roots.
- It does not write current ledger/cycles, target rollups, current evidence, live config, orders, or scale-up.
- It does not create LIVE_READY.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T07:52:22Z
