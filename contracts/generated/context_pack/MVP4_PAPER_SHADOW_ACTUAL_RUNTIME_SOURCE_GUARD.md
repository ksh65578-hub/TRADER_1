# MVP4_PAPER_SHADOW_ACTUAL_RUNTIME_SOURCE_GUARD

context_pack_id: MVP4_PAPER_SHADOW_ACTUAL_RUNTIME_SOURCE_GUARD
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-PAPER-SHADOW-ACTUAL-RUNTIME-SOURCE-GUARD"]
included_schema_ids: ["trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "paper_shadow_evidence_accumulation_validator", "shadow_observation_runtime_orchestration_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/paper_shadow_evidence_accumulation_report.schema.json", "trader1/research/shadow/shadow_runner.py", "trader1/validation/mvp0_validators.py", "tests/validators/test_paper_shadow_evidence_accumulation_validator.py", "tools/emit_paper_shadow_actual_runtime_source_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_PAPER_SHADOW_ACTUAL_RUNTIME_SOURCE_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Paper/shadow long-run eligibility requires validated non-live persistent runtime source evidence.
- Per-window PAPER/SHADOW supporting source ids alone cannot create long-run evidence eligibility.
- Actual runtime source ids cannot be accepted unless their status is VALIDATED_NON_LIVE_RUNTIME.
- Scorecard input remains PAPER-only and cannot create live readiness, live order permission, live trading, or scale-up.

known_omissions_by_design:
- no actual 24h PAPER/SHADOW long-run runtime evidence is created
- no official API verification, account snapshot, credential, live order, live config mutation, or scale-up is used
- ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING remains open

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T07:14:32Z
