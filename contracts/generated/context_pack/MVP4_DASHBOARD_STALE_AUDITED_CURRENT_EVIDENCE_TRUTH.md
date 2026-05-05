# MVP4_DASHBOARD_STALE_AUDITED_CURRENT_EVIDENCE_TRUTH

context_pack_id: MVP4_DASHBOARD_STALE_AUDITED_CURRENT_EVIDENCE_TRUTH
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-DASHBOARD-STALE-AUDITED-CURRENT-EVIDENCE-TRUTH"]
included_schema_ids: ["trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "summary_shell_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/summary_writer.py", "trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py", "tests/dashboard/test_summary_writer.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_dashboard_stale_audited_current_evidence_truth_patch_evidence.py", "contracts/generated/context_pack/MVP4_DASHBOARD_STALE_AUDITED_CURRENT_EVIDENCE_TRUTH.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Audited PAPER current evidence writer output is recognized as implemented when the bound snapshot and idempotency manifest validate.
- Stale audited PAPER values remain visible as STALE display truth rather than being collapsed into UNVERIFIED.
- Fresh audited PAPER values remain VERIFIED display truth only, never LIVE_READY.
- Fresh sources cannot be mislabeled as STALE.
- Ledger or audited current-evidence provenance cannot appear on an UNVERIFIED portfolio card.
- Position details follow the same STALE/VERIFIED distinction as the portfolio snapshot.
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false.

known_omissions_by_design:
- This patch does not generate new PAPER runtime samples.
- This patch does not close any residual open contract gap.
- This patch does not write LIVE_READY, mutate live configuration, call credentials, submit live orders, or permit scale-up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-05T22:10:19Z
