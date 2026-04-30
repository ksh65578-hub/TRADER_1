# BINANCE_ADAPTER_SURFACE_ONLY

context_pack_id: BINANCE_ADAPTER_SURFACE_ONLY
task_class: MVP4_BINANCE_ADAPTER_SURFACE_ONLY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_EXCHANGE_ADAPTER", "SECTION_NAMESPACE_SEPARATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-BINANCE-ADAPTER-SURFACE-ONLY"]
included_schema_ids: ["trader1.binance_adapter_surface_report.v1", "trader1.common_defs.v1"]
included_validator_ids: ["binance_adapter_surface_validator", "root_launcher_surface_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/adapters/binance/__init__.py", "trader1/adapters/binance/surface.py", "trader1/runtime/boot/safe_launcher.py", "trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/schema/common.defs.schema.json", "contracts/schema/binance_adapter_surface_report.schema.json", "tests/adapter/test_binance_adapter_surface.py", "contracts/generated/context_pack/BINANCE_ADAPTER_SURFACE_ONLY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Binance adapter namespace exists only as fail-closed SURFACE_ONLY
- Binance SPOT PAPER is visible as not implemented, not tradable
- Binance FUTURES_USDT_M is explicit NOT_IMPLEMENTED/BLOCKED
- Binance root launcher and dashboard expose BINANCE_ADAPTER_SURFACE_ONLY instead of generic readiness wording
- any credential, private API, order adapter, live flag, or scale-up drift blocks validation
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no Binance public market data collector
- no Binance paper broker
- no Binance futures runtime
- no live key loading or private account calls
- no LIVE_READY snapshot write

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T13:40:29Z
