# MVP4_UPBIT_PAPER_VERIFIED_PORTFOLIO_LEDGER_BOOTSTRAP

context_pack_id: MVP4_UPBIT_PAPER_VERIFIED_PORTFOLIO_LEDGER_BOOTSTRAP
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PORTFOLIO_TRUTH", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-VERIFIED-PORTFOLIO-LEDGER-BOOTSTRAP"]
included_schema_ids: ["trader1.paper_ledger_rollup_report.v1", "trader1.paper_portfolio_snapshot.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "paper_ledger_rollup_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/runtime/ledger/paper_ledger_rollup.py", "tests/runtime/test_paper_ledger_rollup.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_rollup_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_portfolio_snapshot.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/summary.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_verified_portfolio_ledger_bootstrap_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_VERIFIED_PORTFOLIO_LEDGER_BOOTSTRAP.md"]

acceptance_checklist:
- Session-cycle PAPER ledger rollup binds its portfolio provenance to latest_paper_ledger_head.json even when filename ordering differs.
- The canonical dashboard portfolio is VERIFIED only from a fresh PASS PAPER ledger rollup.
- Initial configured PAPER capital remains a starting amount, not a live exchange balance.
- Post-rerun and long-run blockers remain visible; live orders and scale-up remain blocked.

known_omissions_by_design:
- This patch does not resolve post-rerun operator reconciliation guidance.
- This patch does not create long-run evidence, LIVE_READY, live config, credentials, orders, or scale-up permission.

runtime_summary:
- rollup_status: PASS
- ledger_head_match_status: PASS
- ledger_head_cycle_id: mvp4-upbit-paper-ledger-head-binding-guard-cycle-2
- portfolio_status: VERIFIED
- cash_available: 845,923 KRW
- equity: 999,923 KRW
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T21:41:16Z
