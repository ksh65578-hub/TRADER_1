# MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS

context_pack_id: MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS
task_class: MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SHADOW-SCHEDULER-LOCK-LEASE-FRESHNESS"]
included_schema_ids: ["trader1.shadow_observation_scheduler_guard_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator"]
included_artifact_ids: ["trader1/research/shadow/shadow_observation_scheduler.py", "contracts/schema/shadow_observation_scheduler_guard_report.schema.json", "tests/research/test_shadow_observation_scheduler.py", "tools/emit_shadow_scheduler_lock_lease_freshness_patch_evidence.py", "contracts/generated/context_pack/MVP4_SHADOW_SCHEDULER_LOCK_LEASE_FRESHNESS.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- SHADOW scheduler reports include explicit lock lease freshness.
- stale or unproven lock lease freshness blocks append action with DUPLICATE_WRITER_RISK.
- schema and tests reject false-safe lock lease status drift.
- persistent SHADOW runtime and actual runtime harness remain live-blocked.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- no real long-run PAPER/SHADOW session is created by this patch
- no credentialed exchange/account/API call is made
- no live order path, live config mutation, optimizer live promotion, or risk scale-up is enabled

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T04:35:48Z
