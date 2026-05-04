# MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK

context_pack_id: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK
task_class: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-IMPLEMENTATION-DEPTH-RECHECK", "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK", "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK"]
included_schema_ids: ["trader1.upbit_paper_runtime_evidence_collection_profile_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_sample_history_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "paper_ledger_rollup_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "tools/run_upbit_paper_runtime_evidence_collection_profile.py", "trader1/dashboard/read_only_dashboard.py", "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py", "tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py", "tests/contract/test_actual_long_run_runtime_evidence_boundary_implementation_depth_recheck.py", "system/evidence/runtime_checks/MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json", "tools/emit_actual_long_run_runtime_evidence_boundary_implementation_depth_recheck_patch_evidence.py", "contracts/generated/context_pack/MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Per-mode PAPER and SHADOW long-run depth evidence is present in the bounded runtime profile.
- Both PAPER and SHADOW remain listed in missing_long_run_modes until actual per-mode long-run floors pass.
- Bounded PAPER and orchestration-only SHADOW evidence cannot count as actual long-run evidence.
- Dashboard shows per-mode missing span/cycle deficits and blocks hidden per-mode gaps.
- ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY remains OPEN and live-affecting.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_snapshot:
- audit_status: PASS
- per_mode_depth_status: BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH
- missing_long_run_modes: ["PAPER", "SHADOW"]
- paper_missing_span_seconds: 86400
- paper_missing_cycle_count: 2878
- shadow_missing_span_seconds: 86400
- shadow_missing_cycle_count: 2880

known_omissions_by_design:
- this patch does not create actual 24h PAPER/SHADOW long-run evidence
- this patch does not close ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY
- this patch does not use credentials, call private endpoints, place live orders, mutate live config, or scale up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-04T09:40:08Z
