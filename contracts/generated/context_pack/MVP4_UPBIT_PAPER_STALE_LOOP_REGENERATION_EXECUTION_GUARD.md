# MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_SAFE_REGENERATION_EXECUTOR
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-EXECUTION-GUARD"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_regeneration_execution_guard.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_reconciliation_validator", "upbit_paper_stale_loop_regeneration_plan_validator", "upbit_paper_stale_loop_execution_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_stale_loop_regeneration_execution_guard.schema.json", "contracts/registry.yaml", "trader1/runtime/paper/upbit_paper_stale_loop_execution_guard.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_execution_guard.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_regeneration_execution_guard.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_stale_loop_execution_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD.md"]

acceptance_checklist:
- The execution guard validates the source plan before any stale loop regeneration executor can run.
- The guard requires source hash match, source retention, create-new-only replacement paths, and scoped Upbit/KRW_SPOT/PAPER paths.
- Existing replacement paths, source hash mismatch, scope escape, operator-review plans, execution mutation, live/order flags, long-run evidence, promotion, and scale-up remain blocked.
- This patch does not regenerate artifacts, delete stale artifacts, overwrite source artifacts, or create long-run PAPER evidence.

known_omissions_by_design:
- no stale loop report was regenerated
- no stale runtime artifact was deleted or overwritten
- no long-run evidence was created
- no private exchange/account/API call or credential was used
- MVP-5 remains blocked on external live-review evidence and operator approval

current_execution_guard_summary:
- guard_status: PASS
- source_plan_status: READY_FOR_SAFE_PAPER_REGENERATION
- planned_regeneration_item_count: 16
- replacement_existing_count: 0
- source_hash_mismatch_count: 0
- execution_performed: false
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T01:00:00Z
