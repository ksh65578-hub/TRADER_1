# MVP4_SUMMARY_PORTFOLIO_PROVENANCE_GUARD

context_pack_id: MVP4_SUMMARY_PORTFOLIO_PROVENANCE_GUARD
task_class: MVP4_SUMMARY_PORTFOLIO_PROVENANCE_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SUMMARY-PORTFOLIO-PROVENANCE-GUARD"]
included_schema_ids: ["trader1.summary.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.patch_result.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "summary_shell_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/summary.schema.json", "trader1/dashboard/summary_writer.py", "trader1/validation/mvp0_validators.py", "tests/dashboard/test_summary_writer.py", "tools/emit_summary_portfolio_provenance_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_SUMMARY_PORTFOLIO_PROVENANCE_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Summary portfolio LEDGER/PASS values must include source_snapshot_hash, source_snapshot_status=PASS, and SIMULATED_PAPER_LEDGER balance kind.
- Summary validator must block missing provenance and arithmetic drift.
- Dashboard portfolio values remain display truth only and cannot create live readiness or scale-up permission.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live execution
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T17:42:27Z
