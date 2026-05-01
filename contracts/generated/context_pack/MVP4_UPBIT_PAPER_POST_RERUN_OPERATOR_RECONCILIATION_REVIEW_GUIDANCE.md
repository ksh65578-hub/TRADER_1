# MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE
task_class: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RECONCILIATION-REVIEW-GUIDANCE"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator", "upbit_paper_post_rerun_operator_reconciliation_review_guidance_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/registry.yaml", "contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.schema.json", "trader1/runtime/paper/upbit_paper_post_rerun_operator_reconciliation_review_guidance.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_review_guidance.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_post_rerun_operator_reconciliation_review_guidance_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE.md"]

acceptance_checklist:
- The guidance consumes only a validated post-rerun reconciliation blocker rollup report.
- Operator review steps preserve POST_RERUN_RECONCILIATION_REQUIRED as the primary blocker.
- Forbidden outputs explicitly block current evidence, current ledger JSONL, latest runtime pointer, LIVE_READY snapshot, live config mutation, and risk scale-up.
- Current evidence write authorized, write allowed, and candidate current-evidence usable counts remain zero.
- No current ledger JSONL, latest runtime pointer, live readiness, live order, or scale-up artifact is written by this guidance.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, promotion patch, LIVE_READY patch, dashboard binding patch, or scale-up patch.
- POST_RERUN_RECONCILIATION_REQUIRED remains open for operator review and later dashboard binding.
- No private exchange/account/API call, credential, live order, live config mutation, or risk scale-up was used.

runtime_summary:
- review_guidance_status: BLOCKED_RECONCILIATION_REVIEW_REQUIRED
- primary_blocker_code: POST_RERUN_RECONCILIATION_REQUIRED
- guidance_item_count: 8
- review_step_count: 4
- forbidden_output_count: 6
- source_rollup_item_count: 8
- source_unique_blocker_count: 5
- current_evidence_write_authorized_count: 0
- current_evidence_write_allowed_count: 0
- candidate_current_evidence_usable_count: 0
- live_order_allowed: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T17:20:50Z
