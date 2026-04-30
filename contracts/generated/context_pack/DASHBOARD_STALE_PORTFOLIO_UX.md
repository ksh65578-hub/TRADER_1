# DASHBOARD_STALE_PORTFOLIO_UX

context_pack_id: DASHBOARD_STALE_PORTFOLIO_UX
task_class: MVP4_DASHBOARD_STALE_PORTFOLIO_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_SUMMARY_SHELL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-SUMMARY-SHELL", "REQ-MVP0-LIVE-BLOCKED-TEST", "REQ-MVP0-VALIDATOR-LOGIC"]
included_schema_ids: ["trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "summary_shell_validator", "read_only_dashboard_validator", "live_blocked_scaffold_validator", "live_blocked_negative_matrix_validator", "root_launcher_surface_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "tests/validators/test_mvp0_validators.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- stale or future-dated summary.json demotes PAPER portfolio values to STALE/UNVERIFIED
- fresh PAPER portfolio display is labeled as simulated PAPER ledger, not exchange or live truth
- validators listed as implemented in current_implementation_state are callable
- dashboard remains display-only and cannot create live readiness or order permission
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no exchange account balance is fetched
- no API key, secret, .env, or credential is used
- no live order, LIVE_READY snapshot, LIVE_ENABLING_PATCH, or live config mutation is introduced

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T22:47:18Z
