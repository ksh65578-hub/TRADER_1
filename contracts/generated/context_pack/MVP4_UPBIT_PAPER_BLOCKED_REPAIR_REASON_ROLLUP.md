# MVP4_UPBIT_PAPER_BLOCKED_REPAIR_REASON_ROLLUP

context_pack_id: MVP4_UPBIT_PAPER_BLOCKED_REPAIR_REASON_ROLLUP
task_class: MVP4_UPBIT_PAPER_REGENERATED_BLOCKED_REPAIR_REPAIR_PLAN
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-REASON-ROLLUP"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_post_regeneration_reconciliation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_post_regeneration_reconciliation_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_stale_loop_post_regeneration_reconciliation_report.schema.json", "trader1/runtime/paper/upbit_paper_stale_loop_post_regeneration_reconciliation.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_post_regeneration_reconciliation.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_post_regeneration_reconciliation_report.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_blocked_repair_reason_rollup_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_BLOCKED_REPAIR_REASON_ROLLUP.md"]

acceptance_checklist:
- Blocked regenerated replacement items expose structured reason codes.
- Ledger, recovery, and cycle reconciliation status are visible per blocked item.
- Report rollup counts blocked repair reason codes.
- Operator action explains whether ledger, recovery, or runtime cycle repair is needed.
- Blocked repairs remain excluded from current evidence and cannot create long-run, live, or scale-up eligibility.

runtime_summary:
- post_reconciliation_status: BLOCKED
- regenerated_current_accepted_count: 10
- regenerated_current_blocked_reconciliation_count: 6
- blocked_repair_reason_counts: [{"reason_code": "LEDGER_ROLLUP_BLOCKED", "count": 6}, {"reason_code": "LEDGER_ROLLUP_RECONCILIATION_REQUIRED", "count": 6}, {"reason_code": "LOOP_RECONCILIATION_REQUIRED", "count": 6}, {"reason_code": "LOOP_STATUS_BLOCKED", "count": 6}, {"reason_code": "PAPER_RUNTIME_RESUME_BLOCKED", "count": 1}, {"reason_code": "PARTIAL_WRITE_RECOVERY_REQUIRED", "count": 1}, {"reason_code": "RECOVERY_GUARD_BLOCKED", "count": 1}]
- current_evidence_usable_count: 10
- excluded_from_current_evidence_count: 6
- live_order_allowed: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch classifies blocked repairs but does not transform blocked repairs into current evidence.
- No private exchange/account/API call or credential was used.
- No source report was deleted or overwritten.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T02:04:38Z
