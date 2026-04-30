# DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING

context_pack_id: DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING
task_class: MVP4_DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-PAPER-EXPOSURE-QUALITY-BINDING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.paper_exposure_quality_report.v1"]
included_validator_ids: ["read_only_dashboard_validator", "paper_exposure_quality_report_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py", "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json", "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json", "contracts/generated/context_pack/DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING.md"]

acceptance_checklist:
- dashboard risk panel shows paper exposure quality status and sample counts
- launcher loads only exact scoped PAPER exposure quality artifact
- cross-session exposure quality artifacts are ignored
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live evidence collection
- no live config mutation
- no scale-up permission
- no exchange account call

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T07:57:29Z
