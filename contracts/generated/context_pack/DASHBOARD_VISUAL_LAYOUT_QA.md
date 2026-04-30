# DASHBOARD_VISUAL_LAYOUT_QA

context_pack_id: DASHBOARD_VISUAL_LAYOUT_QA
task_class: MVP4_DASHBOARD_VISUAL_LAYOUT_QA
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-VISUAL-LAYOUT-QA", "REQ-MVP4-DASHBOARD-FIRST-SCREEN-SIMPLIFICATION", "REQ-MVP4-DASHBOARD-PORTFOLIO-DETAIL-LAYOUT"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tests/dashboard/test_read_only_dashboard.py", "tools/run_dashboard_visual_layout_validators.py", "tools/refresh_runtime_dashboard_html.py", "tools/emit_dashboard_visual_layout_qa_patch_evidence.py", "contracts/generated/context_pack/DASHBOARD_VISUAL_LAYOUT_QA.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- first screen shows portfolio, running status, and live readiness without three cramped columns
- text wrapping and line-height are guarded for operator readability
- detail drawer open/closed state uses stable keys instead of DOM index only
- every generated runtime dashboard HTML passes the visual layout contract
- no live, order, scale-up, or credential behavior is introduced

known_omissions_by_design:
- browser screenshot pixel QA is still blocked by missing local browser automation dependency
- dashboard remains display truth only and cannot become execution truth

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-30T11:16:53Z
