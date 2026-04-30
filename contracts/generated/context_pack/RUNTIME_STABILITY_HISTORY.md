# RUNTIME_STABILITY_HISTORY

context_pack_id: RUNTIME_STABILITY_HISTORY
task_class: MVP4_RUNTIME_STABILITY_HISTORY_SCAFFOLD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_HEARTBEAT", "SECTION_LIVE_FINAL_GUARD", "SECTION_OPERATOR_VISIBILITY"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-HEARTBEAT", "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.runtime_stability_history.v1", "trader1.read_only_dashboard_shell.v1", "trader1.heartbeat.v1"]
included_validator_ids: ["schema_validator", "read_only_dashboard_validator", "heartbeat_validator", "root_launcher_surface_validator", "live_blocked_scaffold_validator", "live_final_guard_validator", "patch_result_schema_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/health/stability_history.py", "contracts/schema/runtime_stability_history.schema.json", "trader1/runtime/boot/safe_launcher.py", "tests/runtime/test_stability_history.py", "tests/dashboard/test_read_only_dashboard.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- stability history is session/exchange/market_type/mode scoped
- samples are hash-linked and max bounded
- scope mismatch or invalid previous history is isolated instead of mixed
- dashboard may claim VALIDATED_HISTORY only after two or more valid samples
- stability history remains display-only and cannot create live or scale-up permission

known_omissions_by_design:
- no live order path is enabled
- no exchange account call, credential load, or live burn-in is performed
- history is runtime health evidence only, not LIVE_READY evidence
- no risk scale-up or optimizer/convergence live mutation is introduced

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T23:33:53Z
