context_pack_id: MONITOR_STALE_SOURCE_WRITER_GUARD
task_class: RUNTIME_SAFETY_PATCH
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

Included sections:
- SECTION_RUNTIME_RECOVERY
- SECTION_DASHBOARD_OPERATOR_UX
- SECTION_LIVE_FINAL_GUARD

Acceptance checklist:
- stale source monitor cannot overwrite runtime dashboard artifacts
- heartbeat reports SOURCE_IDENTITY_MISMATCH when stale
- dashboard shell keeps live flags false
- runtime schema validator passes current PAPER artifacts
