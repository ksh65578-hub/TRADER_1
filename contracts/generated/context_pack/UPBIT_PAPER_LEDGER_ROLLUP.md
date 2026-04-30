# UPBIT_PAPER_LEDGER_ROLLUP

context_pack_id: UPBIT_PAPER_LEDGER_ROLLUP
task_class: MVP4_UPBIT_PAPER_LEDGER_ROLLUP
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP"]
included_schema_ids: ["trader1.paper_ledger_rollup_report.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.upbit_paper_persistent_loop_report.v1"]
included_validator_ids: ["paper_ledger_rollup_validator", "ledger_durability_validator", "upbit_paper_persistent_loop_validator", "read_only_dashboard_validator"]
included_artifact_ids: ["trader1/runtime/ledger/execution_ledger.py", "trader1/runtime/ledger/paper_ledger_rollup.py", "trader1/runtime/portfolio/paper_portfolio.py", "trader1/runtime/paper/upbit_paper_persistent_loop.py", "trader1/runtime/boot/safe_launcher.py", "trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/schema/paper_ledger_rollup_report.schema.json", "contracts/schema/paper_portfolio_snapshot.schema.json", "contracts/schema/upbit_paper_persistent_loop_report.schema.json", "tests/runtime/test_execution_ledger.py", "tests/runtime/test_paper_portfolio.py", "tests/runtime/test_paper_ledger_rollup.py", "tests/runtime/test_safe_launcher.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "contracts/generated/context_pack/UPBIT_PAPER_LEDGER_ROLLUP.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- cycle-scoped PAPER ledger JSONL rolls up into one display-only portfolio snapshot
- duplicate event/order IDs across cycle files block with RECONCILIATION_REQUIRED
- partial/corrupt ledger JSONL blocks with PARTIAL_WRITE_RECOVERY_REQUIRED
- launcher dashboard prefers the fresh scoped rollup portfolio over a single latest cycle
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no exchange account reconciliation
- no live readiness or live order permission
- no long-run evidence eligibility from this short rollup

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T13:23:32Z
