# MVP4_UPBIT_PAPER_PORTFOLIO_CURRENT_EVIDENCE_BRIDGE_UX

context_pack_id: MVP4_UPBIT_PAPER_PORTFOLIO_CURRENT_EVIDENCE_BRIDGE_UX
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PORTFOLIO_TRUTH", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-PORTFOLIO-CURRENT-EVIDENCE-BRIDGE-UX"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_post_rerun_resolution_current_evidence_closure_validator", "upbit_paper_post_rerun_current_evidence_closure_recheck_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_portfolio_current_evidence_bridge_ux_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_PORTFOLIO_CURRENT_EVIDENCE_BRIDGE_UX.md"]

acceptance_checklist:
- The dashboard keeps configured PAPER capital visible when portfolio values are not current-evidence verified.
- Ledger provenance PASS from the recheck is displayed as support-only and cannot promote cash/equity to VERIFIED.
- Portfolio source snapshot status becomes BLOCKED when post-rerun current-evidence closure recheck blocks the bridge.
- Operation status mirrors the portfolio blocker.
- Live orders, live trading, and scale-up remain false.

known_omissions_by_design:
- This patch does not write current evidence, resolve reconciliation, create LIVE_READY, mutate live config, or scale risk.
- It does not convert configured PAPER capital into live exchange balance or verified current cash/equity.
- No credentialed exchange/account/API call or live order path is used.

runtime_summary:
- dashboard_blocking_reason: POST_RERUN_RECONCILIATION_REQUIRED
- portfolio_status: UNVERIFIED
- portfolio_source_snapshot_status: BLOCKED
- portfolio_blocking_reason: POST_RERUN_RECONCILIATION_REQUIRED
- recheck_status: BLOCKED_POST_RERUN_CLOSURE_CONFIRMED
- current_evidence_bridge_status: BLOCKED_BY_POST_RERUN_CLOSURE
- portfolio_recheck_status: LEDGER_PROVENANCE_PASS_BUT_OPERATOR_CURRENT_EVIDENCE_BLOCKED
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T23:04:14Z
