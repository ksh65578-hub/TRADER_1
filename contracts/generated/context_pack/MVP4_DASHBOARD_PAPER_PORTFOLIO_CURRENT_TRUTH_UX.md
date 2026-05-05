# MVP4_DASHBOARD_PAPER_PORTFOLIO_CURRENT_TRUTH_UX

context_pack_id: MVP4_DASHBOARD_PAPER_PORTFOLIO_CURRENT_TRUTH_UX
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-PAPER-PORTFOLIO-CURRENT-TRUTH-UX"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_paper_portfolio_current_truth_ux_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_PAPER_PORTFOLIO_CURRENT_TRUTH_UX.md"]

acceptance_checklist:
- Configured PAPER capital remains visible as a known PAPER configuration baseline.
- UNVERIFIED is scoped to current cash, equity, PnL, return, and positions when fresh ledger/current-evidence proof is missing.
- Stale or missing current portfolio evidence remains fail-closed and cannot appear as VERIFIED.
- The dashboard keeps live_order_ready=false, live_order_allowed=false, can_live_trade=false, and scale_up_allowed=false.

known_omissions_by_design:
- This patch does not refresh stale PAPER runtime evidence.
- This patch does not mark current cash/equity as verified from configured capital alone.
- This patch does not write current evidence, mutate live config, enable live orders, use credentials, or permit scale-up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-05T02:10:46Z
