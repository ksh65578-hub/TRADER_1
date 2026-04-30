# MVP4_PAPER_PORTFOLIO_POSITION_ROLLUP_GUARD

context_pack_id: MVP4_PAPER_PORTFOLIO_POSITION_ROLLUP_GUARD
task_class: MVP4_UPBIT_PAPER_RUNTIME_PORTFOLIO_ROLLUP_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PAPER-PORTFOLIO-POSITION-ROLLUP-GUARD"]
included_schema_ids: ["trader1.paper_portfolio_snapshot.v1", "trader1.upbit_paper_runtime_cycle_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "paper_portfolio_snapshot_validator", "upbit_paper_runtime_cycle_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/paper_portfolio_snapshot.schema.json", "trader1/runtime/portfolio/paper_portfolio.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_paper_portfolio.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "tools/emit_paper_portfolio_position_rollup_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_PAPER_PORTFOLIO_POSITION_ROLLUP_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER position rows must reconcile quantity, mark price, market value, cost basis, and unrealized PnL.
- Top-level position_market_value and unrealized_pnl must equal the sum of position rows.
- Position rows must remain PAPER-only, long spot, and display truth only.
- Runtime cycle validation must fail closed when nested position detail is tampered.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live execution
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T19:22:40Z
