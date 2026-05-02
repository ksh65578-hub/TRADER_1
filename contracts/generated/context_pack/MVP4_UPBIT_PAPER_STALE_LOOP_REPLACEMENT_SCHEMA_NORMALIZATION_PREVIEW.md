# MVP4_UPBIT_PAPER_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-REPLACEMENT-SCHEMA-NORMALIZATION-PREVIEW"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_replacement_schema_normalization_preview_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_ledger_recheck_preview_validator", "upbit_paper_stale_loop_replacement_schema_normalization_preview_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_stale_loop_replacement_schema_normalization_preview_report.schema.json", "trader1/runtime/paper/upbit_paper_stale_loop_replacement_schema_normalization_preview.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_replacement_schema_normalization_preview.py", "tools/emit_upbit_paper_stale_loop_replacement_schema_normalization_preview_patch_evidence.py", "tools/run_upbit_paper_runtime_evidence_collection_profile.py", "trader1/runtime/smoke.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_replacement_schema_normalization_preview_report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_REPLACEMENT_SCHEMA_NORMALIZATION_PREVIEW.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Replacement persistent-loop missing-field failures are normalized in memory only.
- Normalized candidates no longer fail SCHEMA_IDENTITY_MISMATCH, but remain blocked by reconciliation.
- No replacement file, current evidence, live config, order path, credential path, or scale-up path is written or enabled.

runtime_summary:
- preview_status: BLOCKED
- normalization_candidate_count: 5
- missing_field_total_count: 35
- normalized_schema_fail_count: 0
- normalized_reconciliation_blocked_count: 5
- normalization_write_allowed_count: 0
- current_evidence_write_allowed_count: 0
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch is preview-only. It does not rewrite replacement reports or promote any current evidence.
- It does not resolve post-normalization reconciliation or create LIVE_READY.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T06:01:05Z
