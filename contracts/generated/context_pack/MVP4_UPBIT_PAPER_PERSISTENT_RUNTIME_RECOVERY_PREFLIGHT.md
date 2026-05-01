# MVP4_UPBIT_PAPER_PERSISTENT_RUNTIME_RECOVERY_PREFLIGHT

context_pack_id: MVP4_UPBIT_PAPER_PERSISTENT_RUNTIME_RECOVERY_PREFLIGHT
task_class: MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_EVIDENCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-PERSISTENT-RUNTIME-RECOVERY-PREFLIGHT"]
included_schema_ids: ["trader1.upbit_paper_persistent_loop_report.v1", "trader1.upbit_paper_runtime_recovery_guard_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_paper_persistent_loop_validator", "upbit_paper_runtime_recovery_guard_validator", "upbit_paper_stale_loop_safe_regeneration_executor_validator", "upbit_paper_missing_cycle_rerun_guard_validator", "upbit_paper_bounded_rerun_staging_executor_validator", "upbit_paper_post_rerun_ledger_rollup_reconciliation_validator", "upbit_paper_post_rerun_current_evidence_promotion_guard_validator", "runtime_schema_instance_validator", "ledger_durability_validator", "ledger_reconciliation_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["trader1/runtime/paper/upbit_paper_persistent_loop.py", "trader1/runtime/paper/upbit_paper_stale_loop_safe_regeneration_executor.py", "contracts/schema/upbit_paper_persistent_loop_report.schema.json", "trader1/validation/mvp0_validators.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tools/emit_upbit_paper_persistent_runtime_recovery_preflight_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_PERSISTENT_RUNTIME_RECOVERY_PREFLIGHT.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Persistent Upbit PAPER loop runs a preflight recovery guard when prior runtime state exists.
- Clean prior PAPER state allows bounded PAPER-only current evidence writes.
- Orphan temp files or corrupted PAPER ledger JSONL block before new cycle/latest/ledger current evidence is written.
- Loop report exposes preflight status, guard hash, blocker, and current_evidence_write_allowed.
- Safe stale-loop regeneration preserves or injects preflight fields when repairing legacy loop reports to the current schema.
- Live readiness, live orders, live trading, and scale-up remain false.

known_omissions_by_design:
- This patch does not resolve post-rerun reconciliation.
- This patch does not create long-run evidence, LIVE_READY, live order permission, credential loading, live config mutation, or scale-up.
- Staged post-rerun candidates remain unusable as current evidence until reconciliation evidence is closed.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T18:58:32Z
