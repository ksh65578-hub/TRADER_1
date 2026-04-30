# DASHBOARD_PARAMETER_NARROWING_VISIBILITY

context_pack_id: DASHBOARD_PARAMETER_NARROWING_VISIBILITY
task_class: MVP4_DASHBOARD_PARAMETER_NARROWING_VISIBILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PARAMETER_NARROWING", "SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-PARAMETER-NARROWING-VISIBILITY"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "read_only_dashboard_validator", "parameter_narrowing_validator", "optimizer_guardrail_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "live_final_guard_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_parameter_narrowing_visibility_patch_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html", "system/evidence/audit_reports/MVP4_DASHBOARD_PARAMETER_NARROWING_VISIBILITY_20260429.md", "contracts/generated/context_pack/DASHBOARD_PARAMETER_NARROWING_VISIBILITY.md"]

acceptance_checklist:
- Dashboard shows Parameter Narrowing with dependency closure, sample coverage, and parameter count change.
- PAPER parameter review eligibility is visually blue/normal only when dependency validators, sample bounds, and narrowing bounds pass.
- Parameter write scope is PROPOSAL_ONLY and cannot mutate active or live config.
- LIVE_READY, live order permission, order submission, live config mutation, and scale-up remain false.

known_omissions_by_design:
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-29T06:19:27Z
