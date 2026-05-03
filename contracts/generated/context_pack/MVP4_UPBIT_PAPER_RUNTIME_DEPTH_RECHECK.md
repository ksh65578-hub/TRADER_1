# MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK
task_class: MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-RUNTIME-DEPTH-RECHECK"]
included_schema_ids: ["trader1.upbit_paper_persistent_loop_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_cycle_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_persistent_loop_report.schema.json", "trader1/runtime/paper/upbit_paper_persistent_loop.py", "trader1/runtime/paper/upbit_paper_stale_loop_normalized_reconciliation_recheck.py", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py", "tools/emit_upbit_paper_runtime_depth_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- persistent loop cycle_results expose public-collection input hashes and canonical event depth
- persistent loop cycle_results expose feature hash, regime, selected candidate, and strategy/regime/cost linkage
- validator blocks static-fixture summary mutation, source/runtime hash mismatch, missing canonical depth, and linkage live flags
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

audit_status: PASS

known_omissions_by_design:
- no long-run evidence eligibility is created
- no live order path, credential load, or LIVE_READY snapshot write is introduced
- scale-up remains blocked

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-03T12:25:31Z
