# MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_REPORT_RECONCILIATION
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-RUNTIME-SAMPLE-HISTORY-PROVENANCE"]
included_schema_ids: ["trader1.upbit_paper_runtime_sample_history.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_sample_history_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_runtime_sample_history.schema.json", "contracts/registry.yaml", "trader1/runtime/paper/upbit_paper_runtime_sample_history.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_runtime_sample_history.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_runtime_sample_history.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_runtime_sample_history_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_SAMPLE_HISTORY.md"]

acceptance_checklist:
- Upbit PAPER runtime sample history is built from persistent loop reports and runtime cycle JSON files.
- Runtime cycle paths stay inside system/runtime/upbit/krw_spot/paper/<session_id>/.
- Duplicate runtime cycle hashes are counted and blocked instead of inflating evidence.
- Existing stale or invalid loop reports are surfaced as reconciliation blockers.
- actual_long_run_evidence_created=false, long_run_evidence_eligible=false, live_order_allowed=false, scale_up_allowed=false.

known_omissions_by_design:
- this patch does not create long-run evidence
- this patch does not delete stale runtime artifacts
- this patch does not use private exchange/account/API calls or credentials
- MVP-5 remains blocked on external live-review evidence and operator approval

current_runtime_sample_history:
- runtime_sample_status: BLOCKED
- source_loop_report_count: 17
- accepted_cycle_sample_count: 2
- invalid_source_count: 16
- duplicate_cycle_hash_count: 0

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T00:05:56Z
