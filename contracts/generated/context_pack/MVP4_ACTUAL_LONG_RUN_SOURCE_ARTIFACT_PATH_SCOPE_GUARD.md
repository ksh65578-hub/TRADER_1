# MVP4_ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_SCOPE_GUARD

context_pack_id: MVP4_ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_SCOPE_GUARD
task_class: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-ACTUAL-LONG-RUN-SOURCE-ARTIFACT-PATH-SCOPE-GUARD", "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK"]
included_schema_ids: ["trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "paper_shadow_evidence_accumulation_validator", "runtime_schema_instance_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/paper_shadow_evidence_accumulation_report.schema.json", "trader1/research/shadow/shadow_runner.py", "trader1/validation/mvp0_validators.py", "tests/validators/test_paper_shadow_evidence_accumulation_validator.py", "contracts/generated/context_pack/MVP4_ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_SCOPE_GUARD.md", "system/evidence/audit_reports/MVP4_ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_SCOPE_GUARD.md", "tools/emit_actual_long_run_source_artifact_path_scope_guard_patch_evidence.py"]

acceptance_checklist:
- PAPER/SHADOW source artifact paths must use canonical exchange/market/session paths.
- A path that remains under /paper/ or /shadow/ but points at a different session segment must fail closed.
- Actual long-run runtime evidence remains missing and live-blocking.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

path_guard_summary:
- paper_artifact_path_pattern: ^system/runtime/upbit/krw_spot/paper/[^/]+/paper_operation_gate_report\.json$
- shadow_artifact_path_pattern: ^system/runtime/upbit/krw_spot/shadow/[^/]+/shadow_projection\.json$
- artifact_path_scope_drift_status: BLOCKED
- artifact_path_scope_drift_blocker_code: SNAPSHOT_SCOPE_MISMATCH

known_omissions_by_design:
- This guard does not create actual long-run PAPER/SHADOW runtime evidence.
- This guard does not close ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY.
- No API keys, credentials, live orders, live config mutation, or scale-up are used.
- Runtime monitor outputs under system/runtime are not intended patch artifacts.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-03T22:26:01Z
