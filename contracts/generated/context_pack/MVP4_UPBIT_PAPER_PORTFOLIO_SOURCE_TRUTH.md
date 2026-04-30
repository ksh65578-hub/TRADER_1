# MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH

context_pack_id: MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH
task_class: MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH"]
included_schema_ids: ["trader1.paper_portfolio_snapshot.v1", "trader1.paper_ledger_rollup_report.v1", "trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "runtime_schema_instance_validator", "summary_shell_validator", "paper_portfolio_snapshot_validator", "paper_ledger_rollup_validator", "upbit_paper_runtime_cycle_validator", "upbit_paper_persistent_loop_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/paper_portfolio_snapshot.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "contracts/schema/summary.schema.json", "trader1/runtime/ledger/paper_ledger_rollup.py", "trader1/runtime/portfolio/paper_portfolio.py", "trader1/runtime/paper/upbit_paper_runtime.py", "trader1/dashboard/summary_writer.py", "trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_paper_portfolio.py", "tests/runtime/test_paper_ledger_rollup.py", "tests/integration/test_upbit_paper_runtime_cycle.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/runtime/test_safe_launcher.py", "tests/dashboard/test_summary_writer.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_upbit_paper_portfolio_source_truth_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER portfolio snapshots carry source_runtime_cycle_id and source_paper_ledger_head_hash.
- Upbit PAPER runtime validation blocks portfolio cycle or ledger-head provenance mismatch.
- PAPER ledger rollup validation blocks cumulative portfolio ledger-head provenance mismatch.
- Summary and dashboard preserve source provenance as display truth only.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no live execution
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T21:20:53Z
