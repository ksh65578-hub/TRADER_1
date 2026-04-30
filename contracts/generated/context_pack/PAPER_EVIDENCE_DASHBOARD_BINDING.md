# PAPER_EVIDENCE_DASHBOARD_BINDING

context_pack_id: PAPER_EVIDENCE_DASHBOARD_BINDING
task_class: MVP4_PAPER_EVIDENCE_DASHBOARD_BINDING_HARDENING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_STRATEGY_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PAPER-EVIDENCE-DASHBOARD-BINDING-HARDENING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py", "tools/emit_paper_evidence_dashboard_binding_hardening_patch_evidence.py", "contracts/generated/context_pack/PAPER_EVIDENCE_DASHBOARD_BINDING.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_operation_gate_report.json", "system/evidence/audit_reports/MVP4_PAPER_EVIDENCE_DASHBOARD_BINDING_HARDENING_20260429.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- launcher dashboard reads exact-session paper operation gate evidence when present
- cross-session paper operation gate evidence is ignored rather than mixed
- strategy evidence progress reflects scoped paper/shadow evidence in the UPBIT PAPER launcher
- evidence binding cannot create live or scale permission
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- paper evidence binding is dashboard display truth only and cannot approve live readiness

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-29T03:23:53Z
