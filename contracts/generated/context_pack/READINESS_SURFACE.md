# READINESS_SURFACE

context_pack_id: READINESS_SURFACE
task_class: MVP0_CONTRACT_BASELINE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_READINESS_SURFACE", "SECTION_LIVE_GATE", "SECTION_PATCH_RESULT"]
included_requirement_ids: ["REQ-MVP0-READINESS-SURFACE"]
included_schema_ids: ["trader1.readiness_surface.v1", "trader1.validator_result.v1", "trader1.patch_result.v1"]
included_validator_ids: ["readiness_surface_validator"]
included_artifact_ids: ["trader1/runtime/readiness/readiness_surface.py", "tests/readiness/test_readiness_surface.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- can_start and can_live_review do not imply live_order_ready
- live_order_allowed=true requires live_order_ready=true and can_live_trade=true
- any live blocker keeps live_order_ready=false and live_order_allowed=false
- standalone READY display is forbidden
- live_order_ready remains false
- live_order_allowed remains false
- can_live_trade remains false

known_omissions_by_design:
- live-enabling evidence
- real exchange credentials
- manual order test
- read-only burn-in
- live-ready snapshot writer execution

conflict_resolution_rule:
TRADER_1.md wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T13:08:45Z
