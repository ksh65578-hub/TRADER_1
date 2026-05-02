# MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING

context_pack_id: MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING
task_class: MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-DASHBOARD-BINDING"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_persistent_loop_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_recovery_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "trader1/runtime/paper/upbit_paper_persistent_loop.py", "tests/dashboard/test_read_only_dashboard.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/runtime/test_safe_launcher.py", "tools/emit_upbit_paper_persistent_loop_dashboard_binding_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_PERSISTENT_LOOP_DASHBOARD_BINDING.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Upbit PAPER persistent loop writes a canonical latest loop report for launcher/dashboard discovery.
- Safe launcher loads the scoped canonical or latest loop report without cross-session leakage.
- Read-only dashboard projects bounded PAPER loop status as dashboard display truth only.
- Bounded PAPER loop evidence cannot become long-run evidence, LIVE_READY, live order permission, or scale-up permission.

known_omissions_by_design:
- This patch does not resolve post-rerun reconciliation.
- This patch does not create long-run evidence, LIVE_READY, live order permission, credential loading, live config mutation, or scale-up.
- Binance spot/futures and MICRO_LIVE remain outside this patch.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T01:56:25Z
