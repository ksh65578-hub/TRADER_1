# MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING

context_pack_id: MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PAPER-SHADOW-SUPPORTING-WINDOW-PAIRING"]
included_schema_ids: ["trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "paper_shadow_evidence_accumulation_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/research/shadow/shadow_runner.py", "trader1/validation/mvp0_validators.py", "tests/validators/test_paper_shadow_evidence_accumulation_validator.py", "tools/emit_paper_shadow_supporting_window_pairing_patch_evidence.py", "contracts/generated/context_pack/MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- long-run supporting_source_evidence_ids must contain paired PAPER and SHADOW entries for the same window key
- separate paper-only and shadow-only window counts cannot be treated as paired evidence
- builder, direct validator, and validator self-check use the same pairing rule
- live readiness, live order permission, live trading, and scale-up remain false

known_omissions_by_design:
- no actual long-run runtime evidence is created
- no credentials, exchange account calls, order-capable endpoints, live orders, live config mutation, or scale-up are used

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T08:04:59Z
