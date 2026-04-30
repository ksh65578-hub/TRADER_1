# MVP4_DASHBOARD_PERSISTENT_RUNTIME_DURATION_VISIBILITY

context_pack_id: MVP4_DASHBOARD_PERSISTENT_RUNTIME_DURATION_VISIBILITY
task_class: MVP4_DASHBOARD_PERSISTENT_RUNTIME_DURATION_VISIBILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_DASHBOARD_SHELL
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_RUNTIME_RECOVERY_RTO_ACTIVE
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-DASHBOARD-PERSISTENT-RUNTIME-DURATION-VISIBILITY
- REQ-MVP4-PERSISTENT-RUNTIME-DURATION-EVIDENCE-GUARD
included_schema_ids:
- trader1.read_only_dashboard_shell.v1
included_validator_ids:
- read_only_dashboard_validator
- runtime_schema_instance_validator
- live_final_guard_validator
included_artifact_ids:
- trader1/dashboard/read_only_dashboard.py
- contracts/schema/read_only_dashboard_shell.schema.json
- system/runtime/*/*/*/*/dashboard_shell.json
acceptance_checklist:
- persistent runtime panel is display truth only
- STUB_ESTIMATE_ONLY cannot be shown as long-run runtime evidence
- blocked source runtime reports render BLOCKED, not STUB_ONLY
- existing dashboard_shell runtime artifacts include the new field and valid hash
known_omissions_by_design:
- no real long-run PAPER or SHADOW execution evidence is created
- no live readiness, live order, credential, or scale-up permission is created
conflict_resolution_rule: TRADER_1.md wins over generated context.
