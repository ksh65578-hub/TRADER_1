# MVP4_UPBIT_PAPER_CONFIGURED_PORTFOLIO_UNVERIFIED_EXPLANATION

context_pack_id: MVP4_UPBIT_PAPER_CONFIGURED_PORTFOLIO_UNVERIFIED_EXPLANATION
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-CONFIGURED-PORTFOLIO-UNVERIFIED-EXPLANATION"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_configured_portfolio_unverified_explanation_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_CONFIGURED_PORTFOLIO_UNVERIFIED_EXPLANATION.md"]

acceptance_checklist:
- The dashboard shows configured Upbit PAPER starting capital as 1,000,000 KRW.
- When current cash/equity are UNVERIFIED, the dashboard explains that configured capital is not verified cash or exchange balance.
- A fresh verified simulated ledger remains required before cash/equity are trusted.
- Live orders and scale-up remain blocked.

known_omissions_by_design:
- This patch does not mark stale or missing paper ledger cash as VERIFIED.
- This patch does not write a current ledger, LIVE_READY snapshot, live config, order, or scale-up permission.

runtime_summary:
- portfolio_status: UNVERIFIED
- configured_paper_capital: 1,000,000 KRW
- source_snapshot_freshness_message: Configured PAPER capital is 1,000,000 KRW; current cash and equity require a fresh verified simulated ledger snapshot.
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T21:27:53Z
