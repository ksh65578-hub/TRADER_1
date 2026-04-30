# RUNTIME_REPRODUCIBILITY_SAFE_SMOKE

context_pack_id: RUNTIME_REPRODUCIBILITY_SAFE_SMOKE
task_class: MVP4_RUNTIME_REPRODUCIBILITY_SAFE_SMOKE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_ROOT_LAUNCHER
- SECTION_MVP1_SAFE_BOOT
- SECTION_RUNTIME_STABILITY
- SECTION_SCHEMA_CONTRACTS
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-RUNTIME-REPRODUCIBILITY-SAFE-SMOKE
included_schema_ids:
- trader1.safe_smoke_report.v1
included_validator_ids:
- authority_integrity_validator
- registry_validator
- schema_validator
- root_launcher_guard_validator
- root_launcher_surface_validator
- runtime_schema_instance_validator
- live_final_guard_validator
included_artifact_ids:
- trader1/runtime/smoke.py
- tools/run_safe_smoke.py
- tests/runtime/test_safe_smoke.py
- contracts/schema/safe_smoke_report.schema.json
source_section_hashes:
- SECTION_ROOT_LAUNCHER: 3af875cfc51811cdb559f3ea5f26c74903f5217620ae0a696b16a936ff212104
- SECTION_LIVE_FINAL_GUARD: 9efbc0c1c37e059277712f8d2debf56457147a82ee6b27c5c308eddc621c7141
acceptance_checklist:
- all four root launchers build temporary runtime bundles
- each bundle remains session scoped
- dashboard artifacts remain display truth only
- final_action remains NO_TRADE
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false
known_omissions_by_design:
- no live exchange account access
- no API key or credential loading
- no live order submission
conflict_resolution_rule: TRADER_1.md wins over this context pack.
