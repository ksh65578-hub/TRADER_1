# MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION

context_pack_id: MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION
task_class: MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION"]
included_schema_ids: ["trader1.upbit_paper_post_repair_reconciliation_report.v1", "trader1.upbit_paper_ledger_rollup_repair_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_blocked_repair_plan_validator", "upbit_paper_ledger_rollup_repair_validator", "upbit_paper_post_repair_reconciliation_validator", "paper_ledger_rollup_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/upbit_paper_post_repair_reconciliation_report.schema.json", "trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_post_repair_reconciliation.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_repair_reconciliation_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_post_repair_reconciliation_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION.md"]

acceptance_checklist:
- Repair candidates remain scoped to UPBIT/KRW_SPOT/PAPER.
- Candidate rollup PASS does not become current evidence automatically.
- Source loop expected hash mismatch is operator-visible and validator-enforced.
- Persistent loop, current evidence, long-run evidence, live, and scale-up flags remain blocked.

runtime_summary:
- post_repair_reconciliation_status: BLOCKED
- repair_candidate_count: 1
- candidate_rollup_pass_count: 1
- source_loop_expected_rollup_hash_mismatch_count: 1
- candidate_current_evidence_usable_count: 0
- primary_blocker_code: POST_REPAIR_RECONCILIATION_REQUIRED
- live_order_allowed: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not rewrite replacement loop hashes.
- This patch does not promote repair candidates to current evidence.
- This patch does not delete any review-plan source files.
- No private exchange/account/API call or credential was used.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T04:26:34Z
