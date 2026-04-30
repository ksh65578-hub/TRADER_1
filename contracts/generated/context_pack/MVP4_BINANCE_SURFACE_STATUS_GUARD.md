# MVP4_BINANCE_SURFACE_STATUS_GUARD

context_pack_id: MVP4_BINANCE_SURFACE_STATUS_GUARD
task_class: MVP4_BINANCE_SURFACE_STATUS_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_EXCHANGE_ADAPTER", "SECTION_NAMESPACE_SEPARATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-BINANCE-SURFACE-STATUS-GUARD"]
included_schema_ids: ["trader1.binance_adapter_surface_report.v1", "trader1.root_launcher_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "root_launcher_guard_validator", "root_launcher_surface_validator", "binance_adapter_surface_validator", "runtime_config_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "live_final_guard_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["BINANCE_PAPER.py", "BINANCE_LIVE.py", "trader1/runtime/boot/launcher_guard.py", "trader1/adapters/binance/surface.py", "trader1/validation/mvp0_validators.py", "tests/contract/test_root_launchers.py", "tests/adapter/test_binance_adapter_surface.py", "tools/emit_binance_surface_status_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_BINANCE_SURFACE_STATUS_GUARD.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Binance root launchers disclose SPOT and FUTURES_USDT_M boundary without enabling futures.
- Binance FUTURES_USDT_M remains BLOCKED_NOT_IMPLEMENTED and not root-launchable in MVP-4.
- Dashboard/operator message says FUTURES_USDT_M remains blocked.
- A SPOT-only Binance launcher fixture fails root launcher guard.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: PASS

known_omissions_by_design:
- no Binance public market data collector
- no Binance paper broker
- no Binance futures runtime
- no Binance live adapter
- no credentials or private account calls
- no LIVE_READY snapshot write

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T16:07:08Z
