# MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD

context_pack_id: MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-STALE-LOOP-ISOLATED-EVENT-ID-SCOPE-REPAIRED-CURRENT-EVIDENCE-GUARD"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_stale_loop_isolated_event_id_scope_repaired_duplicate_recheck_validator", "upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator"]
included_artifact_ids: ["contracts/schema/patch_result.schema.json", "contracts/schema/upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.schema.json", "trader1/runtime/paper/upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard.py", "tools/emit_upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_patch_evidence.py", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_stale_loop_isolated_event_id_scope_repaired_current_evidence_guard_report.json", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_STALE_LOOP_ISOLATED_EVENT_ID_SCOPE_REPAIRED_CURRENT_EVIDENCE_GUARD.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Accept repaired duplicate recheck as review-only evidence while denying current evidence writes.
- Keep 3 clean candidates blocked from current ledger, latest runtime pointer, portfolio truth, live permission, and scale-up.
- Preserve post-rerun operator guidance blockers and forbidden outputs.

runtime_summary:
- current_evidence_guard_status: BLOCKED_CURRENT_EVIDENCE_WRITE_DENIED
- candidate_count: 3
- guard_review_ready_count: 3
- guard_blocked_count: 3
- current_evidence_write_allowed_count: 0
- portfolio_truth_write_allowed_count: 0
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not write current evidence, portfolio truth, live config, orders, or scale-up.
- It does not create LIVE_READY or long-run evidence.
- Dashboard binding for this guard remains the next safe task.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-02T10:40:22Z
