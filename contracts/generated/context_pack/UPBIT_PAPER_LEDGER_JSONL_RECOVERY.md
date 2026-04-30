# UPBIT_PAPER_LEDGER_JSONL_RECOVERY

context_pack_id: UPBIT_PAPER_LEDGER_JSONL_RECOVERY
task_class: MVP4_UPBIT_PAPER_LEDGER_JSONL_RECOVERY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LEDGER-JSONL-RECOVERY"]
included_schema_ids: ["trader1.upbit_paper_runtime_recovery_guard_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["upbit_paper_persistent_loop_validator", "ledger_durability_validator", "read_only_dashboard_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/runtime/paper/upbit_paper_persistent_loop.py", "contracts/schema/upbit_paper_runtime_recovery_guard_report.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json", "trader1/dashboard/read_only_dashboard.py", "tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/dashboard/test_read_only_dashboard.py", "contracts/generated/context_pack/UPBIT_PAPER_LEDGER_JSONL_RECOVERY.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- bounded Upbit PAPER runtime cycles write cycle-scoped paper ledger JSONL artifacts
- recovery guard scans paper ledger JSONL and quarantines corrupted partial lines
- invalid or corrupted ledger JSONL blocks PAPER resume and keeps live flags false
- dashboard shows ledger JSONL counts in the PAPER recovery panel

known_omissions_by_design:
- no global cross-cycle ledger rollup promotion
- no live exchange ledger use
- no private endpoint or credential use
- no live order permission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-04-30T12:59:35Z
