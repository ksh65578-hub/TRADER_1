# MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD
task_class: MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-PROMOTION-GUARD"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_current_evidence_promotion_guard_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_post_rerun_ledger_rollup_reconciliation_validator", "upbit_paper_post_rerun_current_evidence_promotion_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_post_rerun_current_evidence_promotion_guard_report.schema.json", "trader1/runtime/paper/upbit_paper_post_rerun_current_evidence_promotion_guard.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_post_rerun_current_evidence_promotion_guard.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_current_evidence_promotion_guard_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_post_rerun_current_evidence_promotion_guard_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD.md"]

acceptance_checklist:
- The guard consumes the validated post-rerun ledger rollup reconciliation report.
- Candidate rollup paths, staged artifact paths, candidate hashes, and planned current-ledger paths are verified.
- Review-ready candidates stay write-blocked: current_evidence_write_allowed_count=0 and candidate_current_evidence_usable_count=0.
- Current ledger JSONL, latest runtime pointer, persistent loop reports, source artifacts, live permission, promotion, long-run evidence, and scale-up remain immutable.

known_omissions_by_design:
- This patch is not a current-evidence writer and does not make post-rerun candidates usable as current evidence.
- Post-rerun reconciliation remains required before any future reviewed writer patch.
- No private exchange/account/API call, credential, live order, live config mutation, or scale-up was used.

runtime_summary:
- promotion_guard_status: BLOCKED
- source_post_rerun_ledger_rollup_status: PASS
- source_post_rerun_reconciliation_status: BLOCKED
- candidate_item_count: 8
- candidate_rollup_verified_count: 8
- promotion_review_ready_count: 8
- current_evidence_write_allowed_count: 0
- candidate_current_evidence_usable_count: 0
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T15:40:48Z
