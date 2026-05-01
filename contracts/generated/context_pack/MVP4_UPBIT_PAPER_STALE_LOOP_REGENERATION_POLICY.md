# MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_POLICY

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_POLICY
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REGENERATION-POLICY"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_regeneration_plan.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_reconciliation_validator", "upbit_paper_stale_loop_regeneration_plan_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_stale_loop_regeneration_plan.schema.json", "contracts/registry.yaml", "trader1/runtime/paper/upbit_paper_stale_loop_regeneration.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_regeneration.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_regeneration_plan.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_stale_loop_regeneration_policy_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_POLICY.md"]

acceptance_checklist:
- Legacy schema drift loop reports are mapped to new PAPER-only replacement paths.
- Current accepted evidence is excluded from regeneration planning.
- Delete, overwrite, live/order, promotion, long-run, and scale-up flags remain false.
- RECONCILIATION_REQUIRED sources require operator review instead of silent or automatic regeneration.
- This patch writes a plan only; it does not regenerate artifacts or create long-run evidence.

known_omissions_by_design:
- no stale loop report was regenerated
- no stale runtime artifact was deleted or overwritten
- no long-run evidence was created
- no private exchange/account/API call or credential was used
- MVP-5 remains blocked on external live-review evidence and operator approval

current_regeneration_plan_summary:
- plan_status: READY_FOR_SAFE_PAPER_REGENERATION
- regeneration_item_count: 16
- operator_review_item_count: 0
- duplicate_replacement_path_count: 0
- actual_regeneration_performed: false
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T00:40:57Z
