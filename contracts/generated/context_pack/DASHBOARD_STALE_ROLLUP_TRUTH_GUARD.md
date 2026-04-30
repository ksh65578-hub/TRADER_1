# DASHBOARD_STALE_ROLLUP_TRUTH_GUARD

context_pack_id: DASHBOARD_STALE_ROLLUP_TRUTH_GUARD
task_class: MVP4_DASHBOARD_STALE_ROLLUP_TRUTH_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-STALE-ROLLUP-TRUTH-GUARD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.paper_ledger_rollup_report.v1", "trader1.paper_portfolio_snapshot.v1"]
included_validator_ids: ["read_only_dashboard_validator", "paper_ledger_rollup_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/runtime/boot/safe_launcher.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_safe_launcher.py", "contracts/generated/context_pack/DASHBOARD_STALE_ROLLUP_TRUTH_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- stale paper_ledger_rollup_report is not accepted as verified dashboard portfolio truth
- a fresh runtime cycle may still provide verified current PAPER portfolio display data
- when stale rollup exists and fresh runtime cycle is missing, dashboard portfolio is UNVERIFIED
- dashboard remains display truth only and cannot create live permission
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live account snapshot
- no LIVE_READY snapshot write
- no credential or private API read
- no risk scale-up
- no profitability claim

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T13:58:44Z
