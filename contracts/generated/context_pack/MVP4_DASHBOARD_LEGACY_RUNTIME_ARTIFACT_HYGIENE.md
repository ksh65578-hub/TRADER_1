# MVP4_DASHBOARD_LEGACY_RUNTIME_ARTIFACT_HYGIENE

context_pack_id: MVP4_DASHBOARD_LEGACY_RUNTIME_ARTIFACT_HYGIENE
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-LEGACY-RUNTIME-ARTIFACT-HYGIENE"]
included_schema_ids: ["trader1.runtime_dashboard_artifact_hygiene_report.v1"]
included_validator_ids: ["runtime_dashboard_artifact_hygiene_validator", "runtime_schema_instance_validator", "schema_validator", "registry_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/runtime/artifact_hygiene.py", "trader1/validation/mvp0_validators.py", "contracts/schema/runtime_dashboard_artifact_hygiene_report.schema.json", "tests/runtime/test_dashboard_artifact_hygiene.py", "tools/run_runtime_dashboard_artifact_hygiene_validators.py", "tools/emit_dashboard_legacy_runtime_artifact_hygiene_patch_evidence.py", "system/evidence/runtime_artifact_hygiene/runtime_dashboard_artifact_hygiene_report.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Session-scoped launcher dashboard shells are classified as active display artifacts only.
- Legacy dashboard shells without session_id are retained for audit but cannot become execution truth or dashboard-serving truth.
- Unknown dashboard_shell.json paths block hygiene validation until classified.
- Live, order, can_live_trade, and scale-up flags remain false.

known_omissions_by_design:
- legacy runtime artifacts are not deleted in this patch
- no exchange account, credential, API key, live order, or LIVE_ENABLING behavior is used

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T05:43:57Z
