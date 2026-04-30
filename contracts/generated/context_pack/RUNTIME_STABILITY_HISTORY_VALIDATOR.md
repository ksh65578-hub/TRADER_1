# RUNTIME_STABILITY_HISTORY_VALIDATOR

context_pack_id: RUNTIME_STABILITY_HISTORY_VALIDATOR
task_class: MVP4_RUNTIME_STABILITY_HISTORY_VALIDATOR
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_MVP1_HEARTBEAT_SCOPE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-RUNTIME-STABILITY-HISTORY-VALIDATOR", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-HEARTBEAT"]
included_schema_ids: ["trader1.runtime_stability_history.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["registry_validator", "schema_validator", "runtime_stability_history_validator", "read_only_dashboard_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/health/stability_history.py", "trader1/validation/mvp0_validators.py", "contracts/registry.yaml", "contracts/validators/validator_registry.json", "tools/validate_mvp0_contracts.py", "tools/run_runtime_stability_history_validators.py", "tests/validators/test_runtime_stability_history_validator.py", "tools/emit_runtime_stability_history_validator_patch_evidence.py", "contracts/generated/context_pack/RUNTIME_STABILITY_HISTORY_VALIDATOR.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- runtime stability histories are validated through the central validator chain
- live or scale-up flag drift in history artifacts is BLOCKED
- scope mismatch across exchange, market_type, mode, or session_id is BLOCKED
- fake VALIDATED_HISTORY and aggregate-count mismatch are rejected
- validator output cannot create live readiness, live permission, trading permission, or scale-up permission

known_omissions_by_design:
- no live order path is enabled
- no exchange account call, credential load, or live burn-in is performed
- stability history is display truth only and not LIVE_READY evidence

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T23:42:45Z
