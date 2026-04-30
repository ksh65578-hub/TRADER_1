# MVP4_SUMMARY_PORTFOLIO_FRESHNESS_GUARD

context_pack_id: MVP4_SUMMARY_PORTFOLIO_FRESHNESS_GUARD
task_class: MVP4_DASHBOARD_SUMMARY_PORTFOLIO_FRESHNESS_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SUMMARY-PORTFOLIO-FRESHNESS-GUARD"]
included_schema_ids: ["trader1.summary.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "summary_shell_validator", "read_only_dashboard_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/summary.schema.json", "trader1/dashboard/summary_writer.py", "trader1/validation/mvp0_validators.py", "tests/dashboard/test_summary_writer.py", "tools/emit_summary_portfolio_freshness_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_SUMMARY_PORTFOLIO_FRESHNESS_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard summary portfolio must carry source snapshot generated_at and age fields.
- Stale PAPER portfolio snapshots must be downgraded before cash, equity, positions, or PnL are trusted.
- Verified summary portfolio must block missing timestamp provenance and stale age claims.
- All portfolio freshness fields remain PAPER display truth only for UPBIT/KRW_SPOT/PAPER.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live execution
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T19:59:36Z
