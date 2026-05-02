# MVP4_UPBIT_PAPER_PORTFOLIO_TRUTH_RECONCILIATION_CLOSURE

context_pack_id: MVP4_UPBIT_PAPER_PORTFOLIO_TRUTH_RECONCILIATION_CLOSURE
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-PORTFOLIO-TRUTH-RECONCILIATION-CLOSURE", "REQ-MVP4-DASHBOARD-PORTFOLIO-TRUTH-RUNTIME-EVIDENCE", "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.paper_ledger_rollup_report.v1", "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "paper_ledger_rollup_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_upbit_paper_portfolio_truth_reconciliation_closure_patch_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_rollup_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/mvp4-upbit-paper-portfolio-truth-reconciliation-closure.paper_ledger_rollup_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/upbit_paper_ledger_idempotency_runtime_evidence_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_PORTFOLIO_TRUTH_RECONCILIATION_CLOSURE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Verified PAPER portfolio display remains allowed only when the summary snapshot is fresh and bound to matching ledger idempotency runtime evidence.
- Stale-loop/post-rerun reconciliation blockers still block current-evidence writes, trading review, live orders, and scale-up.
- The operator status explains that portfolio values are display truth only and do not prove continuous PAPER engine operation.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not resolve stale-loop reconciliation, post-rerun operator queues, LIVE_READY, MICRO_LIVE, or Binance runtime gaps.
- This patch does not use credentials, private exchange endpoints, real orders, live config mutation, or risk scale-up.

runtime_summary:
- portfolio_status: VERIFIED
- cash: 845,923 KRW
- equity: 999,923 KRW
- position_count: 1
- portfolio_blocking_reason: STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED
- reconciliation_status: BLOCKED
- ledger_idempotency_runtime_evidence_status: PASS
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T04:42:52Z
