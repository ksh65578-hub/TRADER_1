# RISK_EXPOSURE_DRAWDOWN_UX

context_pack_id: RISK_EXPOSURE_DRAWDOWN_UX
task_class: MVP4_RISK_EXPOSURE_DRAWDOWN_UX_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_RISK_EXPOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-RISK-EXPOSURE-DRAWDOWN-UX-HARDENING", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "summary_shell_validator", "read_only_dashboard_validator", "root_launcher_surface_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_risk_exposure_drawdown_ux_patch_evidence.py", "contracts/generated/context_pack/RISK_EXPOSURE_DRAWDOWN_UX.md", "system/evidence/audit_reports/MVP4_RISK_EXPOSURE_DRAWDOWN_UX_HARDENING_20260429.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- dashboard shows Risk Exposure near the first screen
- exposure, drawdown, positions, and scale-up blocked state are visible
- normal risk uses green/blue, warning uses yellow, error uses red
- risk exposure remains display-only and cannot create live or scale-up permission
- stale or unverified portfolio inputs cannot be displayed as LOW_RISK

known_omissions_by_design:
- risk exposure is a PAPER display review, not exchange truth
- no live order, live config mutation, LIVE_READY snapshot, or LIVE_ENABLING_PATCH is introduced
- no API key, secret, .env, credential, or real exchange account call is used

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T02:23:43Z
