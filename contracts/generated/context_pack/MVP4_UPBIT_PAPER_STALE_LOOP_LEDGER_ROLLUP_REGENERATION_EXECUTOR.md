# MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-LEDGER-ROLLUP-REGENERATION-EXECUTOR"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_ledger_rollup_regeneration_plan_validator", "upbit_paper_stale_loop_ledger_rollup_regeneration_executor_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_ROLLUP_REGENERATION_EXECUTOR.md", "contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report.schema.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/ledger_rollup_regeneration_candidates/mvp4-ledger-jsonl-recovery-ui-refresh-regenerated-current-schema.paper_ledger_rollup_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_ledger_rollup_regeneration_executor_report.json", "tests/runtime/test_upbit_paper_stale_loop_ledger_rollup_regeneration_executor.py", "tools/emit_upbit_paper_stale_loop_ledger_rollup_regeneration_executor_patch_evidence.py", "trader1/runtime/paper/upbit_paper_stale_loop_ledger_rollup_regeneration_executor.py", "trader1/validation/mvp0_validators.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The executor attempts ledger-rollup regeneration only into a candidate artifact namespace.
- It records strict rollup input scope failures instead of promoting staged ledgers into current evidence.
- It keeps target rollup writes, current evidence writes, live orders, live trading, and scale-up disabled.

runtime_summary:
- executor_status: BLOCKED
- candidate_rollup_attempt_count: 5
- candidate_rollup_pass_count: 1
- candidate_rollup_blocked_count: 4
- strict_input_scope_blocked_count: 4
- candidate_rollup_artifact_ready_count: 1
- current_evidence_write_allowed_count: 0
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not promote candidate rollups into target ledger-rollup evidence.
- It does not mutate current evidence, persistent loops, live config, credentials, orders, or scale-up.
- It does not create LIVE_READY.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T07:20:59Z
