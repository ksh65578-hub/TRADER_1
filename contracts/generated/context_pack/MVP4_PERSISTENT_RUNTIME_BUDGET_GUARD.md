# MVP4_PERSISTENT_RUNTIME_BUDGET_GUARD

context_pack_id: MVP4_PERSISTENT_RUNTIME_BUDGET_GUARD
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PERSISTENT-RUNTIME-BUDGET-GUARD"]
included_schema_ids: ["trader1.shadow_observation_persistent_runtime_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/research/shadow/shadow_observation_persistent_runtime.py", "trader1/dashboard/read_only_dashboard.py", "tests/research/test_shadow_observation_persistent_runtime.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_persistent_runtime_budget_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_PERSISTENT_RUNTIME_BUDGET_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Persistent SHADOW runtime validator blocks heartbeat interval above max runtime budget.
- Persistent SHADOW runtime validator blocks estimated runtime above max runtime budget.
- Dashboard projection renders budget drift as BLOCKED/ERROR with RESOURCE_LIMIT_BLOCK.
- Stub runtime remains not long-run evidence, not optimizer ranking input, not live permission, and not scale-up evidence.

known_omissions_by_design:
- no actual 24h PAPER/SHADOW long-run runtime evidence is created
- no API keys, credentials, exchange account calls, order-capable endpoints, live orders, live config mutation, or scale-up are used
- ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING remains open

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T07:06:14Z
