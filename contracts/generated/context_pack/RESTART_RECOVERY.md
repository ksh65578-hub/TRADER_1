# RESTART_RECOVERY

context_pack_id: RESTART_RECOVERY
task_class: MVP2_RESTART_RECOVERY_SKELETON
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_READINESS_WAL_BLOCKERS", "SECTION_MVP2_FOUNDATION_WAL_ACTIVE", "SECTION_MVP2_REQUIRED_COMPONENTS_ACTIVE", "SECTION_MVP2_OUTPUT_ARTIFACT_ACTIVE", "SECTION_AGENTS_MVP2_REQUIRED_FILES", "SECTION_AGENTS_RESTART_RECOVERY_FILE_HINT"]
included_requirement_ids: ["REQ-MVP2-RESTART-RECOVERY-SKELETON"]
included_schema_ids: ["trader1.intent_wal_event.v1", "trader1.restart_recovery_report.v1", "trader1.ledger_event.v1"]
included_validator_ids: ["restart_recovery_validator"]
included_artifact_ids: ["trader1/core/events/intent_wal.py", "trader1/core/ledger/restart_recovery.py", "tests/runtime/test_restart_recovery.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- source hashes match before use
- generated context pack is not authority
- restart recovery is UPBIT/KRW_SPOT/PAPER scoped for MVP-2
- intent WAL is hash-linked and paper/live separated
- missing ledger or missing WAL blocks recovery
- recovery never resumes live mode
- adapter calls and live permission mutation remain blocked
- live flags remain false

known_omissions_by_design:
- no exchange API call
- no real live order submission
- no live resume
- no production disaster recovery claim
- retained archive search results were not used as authority and cannot create permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: 2026-04-28T15:23:47Z
