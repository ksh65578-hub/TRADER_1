# MVP4_DASHBOARD_UPBIT_PAPER_RUNTIME_EVIDENCE_PROFILE_BINDING

context_pack_id: MVP4_DASHBOARD_UPBIT_PAPER_RUNTIME_EVIDENCE_PROFILE_BINDING
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-UPBIT-PAPER-RUNTIME-EVIDENCE-PROFILE-BINDING", "REQ-MVP4-UPBIT-PAPER-RUNTIME-EVIDENCE-COLLECTION-PROFILE"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1"]
included_validator_ids: ["schema_validator", "read_only_dashboard_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "system/evidence/runtime_checks/MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html", "contracts/generated/context_pack/MVP4_DASHBOARD_UPBIT_PAPER_RUNTIME_EVIDENCE_PROFILE_BINDING.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard shows bounded Upbit PAPER runtime evidence profile as display-only status.
- Profile PASS remains not LIVE_READY, not long-run evidence, not current-evidence write permission, and not scale-up evidence.
- Duplicate ledger/idempotency evidence projects as RECONCILIATION_REQUIRED.
- Source artifacts and runtime dashboard schema include the profile source.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- profile_status: STALE
- component_pass_count: 4/4
- accepted_cycle_sample_count: 1
- ledger_runtime_evidence_status: PASS
- mismatch_count: 0

known_omissions_by_design:
- no LIVE_READY snapshot is written
- no live order or private exchange API path is used
- no risk scale-up or live config mutation is allowed
- Binance spot/futures remain surface/scaffold gaps

conflict_resolution_rule:
TRADER_1.md active authority wins over this generated context pack.
generated_at_utc: 2026-05-02T03:57:23Z
