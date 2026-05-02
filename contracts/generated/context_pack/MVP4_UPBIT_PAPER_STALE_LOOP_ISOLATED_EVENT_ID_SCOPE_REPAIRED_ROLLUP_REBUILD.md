# MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-ISOLATED-EVENT-ID-SCOPE-REPAIRED-ROLLUP-REBUILD"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_isolated_event_id_scope_repair_executor_validator", "upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report.schema.json", "trader1/runtime/paper/upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild.py", "tools/emit_upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_patch_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_isolated_event_id_scope_repaired_rollup_rebuild_report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_ROLLUP_REBUILD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Six event-id repaired candidate mirror ledger JSONL files are loaded without becoming current evidence.
- Three repaired candidate rollups are written as candidate-only artifacts.
- Duplicate event count is zero after event-id repair.
- Current canonical ledger, target rollup, portfolio truth, live permission, and scale-up remain blocked.

runtime_summary:
- rebuild_status: REPAIRED_CANDIDATE_ROLLUPS_READY_CURRENT_EVIDENCE_BLOCKED
- candidate_rollup_attempt_count: 3
- candidate_rollup_pass_count: 3
- candidate_rollup_blocked_count: 0
- candidate_rollup_artifact_ready_count: 3
- ledger_jsonl_count: 6
- ledger_event_count: 36
- duplicate_event_count: 0
- event_id_updated_count: 12
- current_evidence_write_allowed_count: 0
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not write current ledger/cycles, target rollups, portfolio truth, live config, orders, or scale-up.
- It does not create LIVE_READY or long-run evidence.
- A repaired-rollup duplicate recheck remains the next reconciliation proof step.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T10:06:12Z
