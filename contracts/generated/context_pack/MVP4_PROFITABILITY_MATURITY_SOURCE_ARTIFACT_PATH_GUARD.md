# MVP4_PROFITABILITY_MATURITY_SOURCE_ARTIFACT_PATH_GUARD

context_pack_id: MVP4_PROFITABILITY_MATURITY_SOURCE_ARTIFACT_PATH_GUARD
task_class: MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PROFITABILITY-MATURITY-SOURCE-ARTIFACT-PATH-GUARD", "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT"]
included_schema_ids: ["trader1.profitability_evidence_maturity_rollup.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "profitability_evidence_maturity_rollup_validator", "profitability_optimizer_evidence_gap_validator", "optimizer_no_live_mutation_validator", "optimizer_guardrail_validator", "convergence_assessment_validator", "coverage_index_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/validation/mvp0_validators.py", "tests/validators/test_profitability_optimizer_evidence_gap_validator.py", "tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json", "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json", "tools/emit_profitability_maturity_source_artifact_path_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_PROFITABILITY_MATURITY_SOURCE_ARTIFACT_PATH_GUARD.md"]

acceptance_checklist:
- Profitability maturity rollup component source_artifact_paths must be repo-relative existing files.
- Missing dashboard static HTML evidence must be rebound to the actual read-only dashboard source.
- Negative tests must cover missing component artifacts and repository escape attempts.
- PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY remains open and live-affecting.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

source_artifact_path_summary:
- missing_dashboard_source_path_count_before: 0
- source_artifact_path_rewrite_count: 0
- source_artifact_path_count: 15
- source_artifact_missing_count_after: 0
- source_artifact_escape_count_after: 0
- canonical_dashboard_source_path: trader1/dashboard/read_only_dashboard.py

known_omissions_by_design:
- This guard does not close the profitability evidence maturity gap.
- This guard does not create long-run, OOS, read-only burn-in, manual-order, live, or scale-up evidence.
- Runtime monitor outputs under system/runtime are not intended patch artifacts.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-03T22:02:02Z
