# MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE
task_class: MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-RUNTIME-EVIDENCE-COLLECTION-PROFILE"]
included_schema_ids: ["trader1.upbit_paper_runtime_evidence_collection_profile_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_recovery_guard_validator", "upbit_paper_runtime_sample_history_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "paper_ledger_rollup_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json", "contracts/schema/patch_result.schema.json", "tools/run_upbit_paper_runtime_evidence_collection_profile.py", "tools/emit_upbit_paper_runtime_evidence_collection_profile_patch_evidence.py", "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py", "system/evidence/runtime_checks/MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Bounded Upbit PAPER runtime loop executes from public/static PAPER inputs only.
- Runtime recovery guard, sample history, and ledger idempotency evidence are validated together.
- Duplicate ledger/idempotency evidence is covered by tests and blocks as RECONCILIATION_REQUIRED.
- The profile is explicit bounded evidence only and keeps long_run_evidence_eligible=false.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- profile_status: PASS
- component_pass_count: 4/4
- accepted_cycle_sample_count: 2
- ledger_runtime_evidence_status: PASS
- mismatch_count: 0

known_omissions_by_design:
- no long-run PAPER/SHADOW evidence is created
- no LIVE_READY snapshot is written
- no live config or active/live config mutation is allowed
- no exchange credential, account, private endpoint, or live order path is used
- dashboard binding of this profile remains a later task

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-02T03:28:53Z
