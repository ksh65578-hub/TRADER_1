# MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_GUARD
task_class: MVP4_UPBIT_PAPER_RUNTIME_RECOVERY_AND_LONG_RUN_GUARDS
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LONG_RUN_OPERATION", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-RUNTIME-RECOVERY-GUARD", "REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-BOUNDED", "REQ-MVP4-PUBLIC-CANONICAL-EVENT-JSONL-RECOVERY"]
included_schema_ids: ["trader1.upbit_paper_runtime_recovery_guard_report.v1", "trader1.upbit_paper_persistent_loop_report.v1"]
included_validator_ids: ["upbit_paper_runtime_recovery_guard_validator", "upbit_paper_persistent_loop_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/runtime/paper/upbit_paper_persistent_loop.py", "tests/integration/test_upbit_public_collection_persistent_loop.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- latest PAPER runtime cycle must be parseable, schema-valid, and hash-valid before PAPER resume
- canonical public JSONL partial corruption is quarantined and resume is blocked for reconcile review
- orphan runtime temp files block resume as PARTIAL_WRITE_RECOVERY_REQUIRED
- recovery guard cannot create long-run evidence, promotion eligibility, live readiness, live permission, trading permission, or scale-up permission
- loop report exposes recovery guard status and hash so stale/false-safe resume claims are visible

known_omissions_by_design:
- this is bounded PAPER recovery evidence, not 24/7 long-run evidence
- no live order, private exchange call, API key, credential, or LIVE_ENABLING behavior is performed
- dashboard display integration for the recovery guard remains the next safe UX task

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. Generated context packs are not authority.
generated_at_utc: 2026-04-30T10:29:39Z
