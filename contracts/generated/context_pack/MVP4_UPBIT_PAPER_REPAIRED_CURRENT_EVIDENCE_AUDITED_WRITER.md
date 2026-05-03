# MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER

context_pack_id: MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER
task_class: MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER"]
included_schema_ids: ["trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1", "trader1.upbit_paper_audited_current_evidence_snapshot.v1", "trader1.upbit_paper_audited_current_evidence_idempotency_manifest.v1", "trader1.paper_portfolio_snapshot.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "runtime_schema_instance_validator", "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_validator", "paper_ledger_rollup_validator", "paper_portfolio_snapshot_validator", "upbit_paper_repaired_current_evidence_audited_writer_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/upbit_paper_repaired_current_evidence_audited_writer_report.schema.json", "trader1/runtime/paper/upbit_paper_repaired_current_evidence_audited_writer.py", "trader1/validation/mvp0_validators.py", "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py", "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep.py", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_upbit_paper_repaired_current_evidence_audited_writer_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repaired_current_evidence_audited_writer_report.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/current_evidence/audited_current_evidence_snapshot.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/portfolio/paper_portfolio_snapshot.json"]

acceptance_checklist:
- The audited writer reads validated implementation-prep and PAPER ledger-rollup sources only.
- It writes current evidence, idempotency, and portfolio truth artifacts under the scoped PAPER session.
- It uses the declared temp files plus a scoped single-writer lock and leaves no lock behind.
- Re-running the writer reuses matching outputs instead of rewriting or double-counting evidence.
- Current evidence and portfolio truth remain PAPER-only, display-only, and live-blocked.

runtime_summary:
- writer_status: PASS_AUDITED_CURRENT_EVIDENCE_ALREADY_WRITTEN
- artifact_written_count: 0
- artifact_reused_count: 3
- portfolio_truth_status: VERIFIED_PAPER_LEDGER_ROLLUP
- cash_status: VERIFIED
- equity_status: VERIFIED
- configured_initial_cash_krw: 1000000
- verified_cash_krw: 845923
- verified_equity_krw: 999922.9999999999999999999997
- verified_total_pnl_krw: -77.0000000000000000000003
- portfolio_source: PAPER_LEDGER_ROLLUP
- open_position_count: 1
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not bind the dashboard to the audited writer outputs.
- It does not create LIVE_READY, live config, live orders, private API calls, credentials, long-run evidence, or scale-up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-03T09:47:32Z
